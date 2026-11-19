# BASES-DE-DATOS-NO-RELACIONALES

## Redis Cloud: segundo despliegue

El Redis local (Docker) atiende a los tornos en tiempo real. Redis Cloud reparte los avisos de aforo por Pub/Sub y guarda la caché del aforo para la app pública, porque es accesible desde cualquier móvil y solo necesita datos ligeros.

### Puesta en marcha

1. Crear la base de datos en Redis Cloud (plan Free, en una región europea).
2. Copiar `.env.example` como `.env` en esta carpeta y rellenarlo con el host, el puerto y la contraseña. El `.env` no se sube a GitHub.
3. Comprobar la conexión: `python config_nube.py`
4. Con el compose de Redis arrancado (`docker compose up -d`), comparar la latencia de los dos despliegues: `python medir_latencia.py`

### Ficheros

| Fichero | Para qué sirve |
|---|---|
| `config_nube.py` | Conexión a Redis Cloud (`conectar_nube()`) y nombres de los canales de avisos y de las claves de la caché |
| `medir_latencia.py` | Compara la latencia del Redis local y de Redis Cloud (PING y escritura+lectura) |
| `puente_avisos.py` | Vigila las plazas libres del Redis local y publica un aviso en la nube cuando una sala cambia de nivel |
| `suscriptor_avisos.py` | App de estudiantes: recibe los avisos con PSUBSCRIBE, filtrando por un patrón, y mide la latencia |
| `app_aforo.py` | App pública: consulta las plazas libres de las salas usando Redis Cloud como caché (cache-aside) |
| `probar_acl.py` | Prueba los permisos de cada usuario de las ACL: operaciones permitidas y denegadas (NOPERM) |
| `docker-compose.sentinel.yml` | Añade 3 sentinels al compose de redis local para tener failover automático |
| `sentinel/sentinel.conf` | Configuración de los sentinels: maestro vigilado, quorum 2 y tiempos |
| `.env.example` | Plantilla de credenciales |

### Avisos en tiempo real (Pub/Sub)

Cada sala tiene tres niveles, y cada nivel lleva una prioridad que forma parte del nombre del canal (`aviso:<prioridad>:<campus>:<sala>`):

| Nivel | Cuándo | Prioridad |
|---|---|---|
| `LLENA` | 0 plazas libres | `alta` |
| `CASI_LLENA` | 5 plazas libres o menos | `media` |
| `HAY_SITIO` | Más de 5 plazas libres | `baja` |

Una sala llena no vuelve a tener sitio hasta que haya 3 plazas libres. Así no se manda un aviso cada vez que alguien entra o sale de una sala casi llena.

Para la demo hacen falta tres terminales en esta carpeta, con el compose arrancado y los datos cargados:

1. App: `python suscriptor_avisos.py`. Para filtrar: `python suscriptor_avisos.py aviso:alta:*` (solo salas llenas) o `python suscriptor_avisos.py aviso:*:VIC:*` (solo Vicálvaro).
2. Puente: `python puente_avisos.py`
3. Simulador rápido para que las salas se llenen: `python simulador.py --prob-entrada 0.9 --pausa 0.05`. Para vaciarlas: `python simulador.py --prob-entrada 0.1 --pausa 0.05`.

La app muestra la latencia de cada aviso y la media acumulada. El puente pone la hora de envío en el mensaje y la app calcula `hora de llegada - hora de envío`. Funciona porque los dos se ejecutan en el mismo ordenador, con el mismo reloj.

Pub/Sub no guarda los mensajes: si la app no está conectada, el aviso se pierde. Para avisos es aceptable, porque el estado real sigue en Redis y se puede consultar en cualquier momento.

### Caché del aforo (cache-aside)

La app pública no lee del Redis de los tornos, sino de una caché en Redis Cloud (`cache:aforo:<sala>`, con un TTL de 15 s):

- **Acierto:** el dato está en la caché y se devuelve directamente.
- **Fallo:** el dato no está (nunca se pidió o ya caducó). Se lee del Redis local y se guarda en la nube durante 15 s.

Así, aunque muchos estudiantes consulten a la vez, el Redis de los tornos recibe como mucho una lectura por sala cada 15 segundos. A cambio, el dato puede tener hasta 15 s de antigüedad. Para que no se vea un dato viejo justo cuando una sala se llena o se vacía, el puente de avisos borra la entrada de la caché de esa sala cada vez que cambia de nivel.

Para probarla, con el simulador y el puente en marcha:

1. `python app_aforo.py VIC-BIB-S2`, dos veces seguidas: la primera es un fallo y la segunda un acierto, con el tiempo que le queda en la caché. Pasados 15 s vuelve a fallar.
2. `python app_aforo.py`: simula 200 consultas de estudiantes a salas al azar y resume los aciertos, los fallos y el tiempo medio de cada uno.

### Control de acceso (ACL)

En Redis Cloud hay cuatro usuarios, cada uno con un rol propio y una regla ACL que solo permite lo imprescindible (mínimo privilegio). Los roles predefinidos (Full-Access, Read-Write y Read-Only) no se usan.

| Usuario | Rol | Lo usa | Regla ACL |
|---|---|---|---|
| `backend` | `rol-backend` | `puente_avisos.py`, `app_aforo.py` | `+ping +get +set +del +ttl +publish ~cache:* resetchannels &aviso:*` |
| `app` | `rol-app` | `suscriptor_avisos.py` (móvil del estudiante) | `+ping +get +ttl +psubscribe ~cache:* resetchannels &aviso:* &aviso:alta:* &aviso:media:* &aviso:baja:* &aviso:*:MOS:* &aviso:*:FUE:* &aviso:*:VIC:*` |
| `bibliotecario` | `rol-bibliotecario` | Personal de la biblioteca | `+ping +get +ttl +del +publish ~cache:* resetchannels &aviso:*` |
| `analista` | `rol-analista` | Monitorización | `+ping +info +@read ~* resetchannels` |

- `backend` escribe la caché y publica los avisos, pero no puede tocar claves fuera de `cache:` ni publicar en otros canales.
- `app` solo lee la caché y se suscribe a los avisos: no puede escribir ni publicar avisos falsos.
- `bibliotecario` puede publicar avisos manuales (por ejemplo, "sala cerrada") y borrar el dato de una sala de la caché para forzar que se actualice, pero no puede inventarse el aforo (`SET`).
- `analista` puede leer cualquier clave y las estadísticas del servidor (`INFO`), pero no puede escribir, borrar ni publicar.

Dos detalles de las reglas:

- **`resetchannels`**: Redis Cloud deja Pub/Sub abierto por defecto, incluso en Redis 7. Sin `resetchannels`, cualquier usuario podría escuchar o publicar en cualquier canal. Por eso cada regla empieza bloqueando todos los canales y después permite solo los de avisos (`&aviso:*`).
- **Patrones de `PSUBSCRIBE`**: Redis exige que el patrón de una suscripción aparezca tal cual en la regla. `&aviso:*` no basta para suscribirse a `aviso:alta:*`. Por eso la regla de `app` lista los filtros permitidos: todos los avisos, por prioridad y por campus.

El usuario `default` está desactivado. Cada programa entra con su usuario (`conectar_nube("backend")`, `conectar_nube("app")`) y su contraseña del `.env`.

Para comprobar los permisos: `python probar_acl.py`. Con cada usuario intenta operaciones permitidas y prohibidas, muestra `PERMITIDO` o `DENEGADO (NOPERM ...)` y comprueba al final que el usuario `default` está desactivado.

### Sentinel: failover automático

Con el failover manual, si el maestro se cae alguien tiene que promocionar una réplica (`REPLICAOF NO ONE`). Con Sentinel se hace solo. Tres sentinels vigilan al maestro y, si deja de responder, eligen una réplica y la convierten en el nuevo maestro.

- **3 sentinels y quorum 2.** Un sentinel solo no puede dar el maestro por caído: puede que el problema sea suyo (por ejemplo, de red). Tienen que estar de acuerdo al menos 2 (el quorum). Después, uno de ellos tiene que ser elegido líder por la mayoría (2 de 3) para hacer el failover. Con 3 sentinels se sigue funcionando aunque uno se caiga.
- **5 segundos** sin respuesta para considerar caído un nodo (`down-after-milliseconds`).
- **IPs fijas.** Cada contenedor tiene una IP fija en la red `172.30.0.0/24`: el maestro es `172.30.0.2`, las réplicas `.3` y `.4`, y los sentinels `.11`, `.12` y `.13`. Las réplicas y los sentinels se conectan por IP (ver "Problema encontrado").
- **El compose de Redis local no se modifica.** `docker-compose.sentinel.yml` se combina con él: añade los sentinels, da IPs fijas a los tres nodos y hace que las réplicas apunten a la IP del maestro.

Prueba, en esta carpeta y con Docker Desktop abierto:

1. Arrancar los nodos y los sentinels: `docker compose -f docker-compose.yml -f docker-compose.sentinel.yml up -d`
2. Unos 15 segundos después, comprobar el estado:
   - `docker exec sentinel1 redis-cli -p 26379 INFO sentinel` debe mostrar `address=172.30.0.2:6379,slaves=2,sentinels=3`.
   - `docker exec sentinel1 redis-cli -p 26379 SENTINEL ckquorum aforo` debe responder `OK 3 usable Sentinels`.
3. Tirar el maestro: `docker stop redis-master`.
4. Unos 15 segundos después, `docker exec sentinel1 redis-cli -p 26379 SENTINEL get-master-addr-by-name aforo` ya no responde `172.30.0.2`, sino la IP de la réplica promocionada (`172.30.0.3` o `172.30.0.4`).
5. Ver cómo lo decidieron: `docker logs sentinel1 | Select-String "odown|switch"` muestra `+odown ... #quorum` y `+switch-master`.

Al terminar, volver al compose normal: `docker compose -f docker-compose.yml -f docker-compose.sentinel.yml down` y después `docker compose up -d`.

#### Problema encontrado

La primera versión usaba los nombres de los contenedores (`redis-master`...) en lugar de IPs. Al parar el maestro, su nombre deja de existir, y Docker tarda varios segundos en responder que no existe. Mientras, las réplicas (que intentan reconectarse a `redis-master` cada segundo) y los sentinels se quedaban bloqueados esperando la respuesta. Los sentinels creían caídas también las réplicas y a otros sentinels, entraban en modo TILT y no hacían el failover. Con IPs fijas no hay que buscar ningún nombre.
