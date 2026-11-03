# Dataset sintético: aforo de salas de estudio

Datos para la Parte B (Apache Cassandra) de la práctica. Simulan el uso de las salas de estudio de tres campus entre el 13 de abril y el 26 de junio de 2026: un periodo de clases, la preparación de exámenes, la convocatoria ordinaria y el inicio de la extraordinaria.

**Origen:** generado con IA (Claude), tal como permite el enunciado ("Generar un dataset sintético (PEDIR A LA IA)"). Los campus existen, pero las salas, las capacidades, los horarios y los estudiantes son inventados. Ningún dato corresponde a personas reales.

## Ficheros

| Fichero | Filas | Contenido | Consultas (Q1–Q6) |
|---|---:|---|---|
| `accesos.csv` | 61.949 | Una fila por visita: quién, qué sala y puesto, entrada y salida | Q3 (`visitas`) |
| `ocupacion_sala_15min.csv` | 29.262 | Ocupación de cada sala cada 15 minutos | Q1 y Q2 (`ocupacion_sala`) |
| `load_top_salas_dia.csv` | 612 | Resumen por campus y día, pensado para ranking por pico | Q4 (`top_salas_dia`) |
| `load_resumen_sala.csv` | 612 | Resumen por sala y día, pensado para consulta por sala y mes | Q5 (`resumen_sala`) |
| `uso_puestos_mes.csv` | 2.196 | Usos de cada puesto por sala y mes | Q6 (`puestos_mes`) |
| `salas.csv` | 11 | Catálogo de salas | Referencia y simulador de Redis |
| `puestos.csv` | 732 | Catálogo de puestos (mesa, enchufe, ventana) | Referencia y simulador de Redis |
| `estudiantes.csv` | 2.380 | Estudiantes (campus, titulación, curso) | Referencia y simulador de Redis |

`accesos.csv` es el dato base. Los ficheros derivados (ocupación, resúmenes diarios y uso de puestos) se han calculado a partir de él y coinciden exactamente.

`load_top_salas_dia.csv` y `load_resumen_sala.csv` son dos ficheros desnormalizados a partir del mismo histórico diario: cada uno trae solo las columnas que necesita su tabla en Cassandra (claves distintas: por campus/día para el top, por sala/mes para el resumen). Es un ejemplo claro de modelado orientado a consulta.

## Diccionario de datos

El tipo indicado es el tipo de CQL con el que cada columna se carga sin problemas.

### accesos.csv

| Columna | Tipo | Descripción |
|---|---|---|
| estudiante_id | text | `EST00001` … `EST02380` |
| mes | text | `YYYY-MM` de la fecha. Sirve para acotar el tamaño de partición |
| ts_entrada | timestamp | Momento de entrada, **en UTC** (ver notas de carga) |
| ts_salida | timestamp | Momento de salida, en UTC |
| fecha | date | Día de la visita, en hora local de Madrid |
| campus | text | `MOS`, `FUE` o `VIC` |
| sala_id | text | Por ejemplo, `MOS-BIB-S1` |
| puesto | int | De 1 a la capacidad de la sala. En un bitmap de Redis, el offset sería puesto − 1 |
| duracion_min | int | Minutos de estancia |
| salida_en_cierre | boolean | `True` si la salida coincide con la hora de cierre de la sala |
| redirigido | boolean | `True` si el estudiante entró tras encontrar llena otra sala del campus |

### ocupacion_sala_15min.csv

| Columna | Tipo | Descripción |
|---|---|---|
| sala_id | text | |
| fecha | date | Hora local |
| hora | time | `HH:MM:SS` local, cada 15 minutos desde la apertura hasta el último cuarto antes del cierre |
| ocupados | int | Puestos ocupados en ese instante |
| libres | int | Capacidad − ocupados |
| porcentaje | float | Ocupación en %, con un decimal |

Equivale a lo que guardaría un proceso que cada 15 minutos lee el BITCOUNT de cada sala en Redis y lo vuelca a Cassandra. Es una forma natural de conectar las dos partes en la presentación.

### load_top_salas_dia.csv

| Columna | Tipo | Descripción |
|---|---|---|
| campus | text | |
| fecha | date | |
| pico_pct | float | Pico en % de la capacidad |
| sala_id | text | |
| capacidad | int | |
| pico_ocupados | int | Máxima ocupación simultánea |
| ocupacion_media_pct | float | Ocupación media del día |
| entradas | int | Visitas que empezaron ese día |

Pensado para la tabla `top_salas_dia` (partition `(campus, fecha)`, clustering por `pico_pct` DESC).

### load_resumen_sala.csv

| Columna | Tipo | Descripción |
|---|---|---|
| sala_id | text | |
| mes | text | `YYYY-MM` |
| fecha | date | |
| campus | text | |
| periodo | text | `CLASES`, `REPASO`, `EXAMENES`, `ENTRE_CONVOCATORIAS` o `EXTRAORDINARIA` |
| capacidad | int | |
| entradas | int | |
| pico_pct | float | |
| ocupacion_media_pct | float | |
| minutos_completa | int | Minutos con la sala al 100 % |

Pensado para la tabla `resumen_sala` (partition `(sala_id, mes)`, clustering por `fecha`).

### uso_puestos_mes.csv

| Columna | Tipo | Descripción |
|---|---|---|
| sala_id | text | |
| mes | text | `YYYY-MM` |
| usos | int | Número de visitas en ese puesto ese mes |
| puesto | int | |
| minutos_uso | int | Minutos totales de uso |
| enchufe | boolean | |
| ventana | boolean | |

### Catálogos

- **salas.csv:** sala_id, campus, campus_nombre, nombre, capacidad (int), hora_apertura, hora_cierre, hora_cierre_examenes (time) y abre_sabados_examenes (boolean).
- **puestos.csv:** sala_id, puesto (int), mesa (int, mesas de 4), enchufe y ventana (boolean).
- **estudiantes.csv:** estudiante_id, campus, titulacion y curso (int, de 1 a 4). Hay 8 estudiantes sin ninguna visita, como pasaría en la realidad.

## Notas para la carga con `COPY ... FROM ... WITH HEADER=TRUE`

1. **La primera fila es la cabecera.** Todos los ficheros usan coma como separador, punto decimal y UTF-8 (hay tildes en los nombres). No hay celdas vacías ni comillas.
2. **COPY asigna las columnas por posición, no por nombre.** Si en la tabla las columnas van en otro orden, indicad en el COPY la lista de columnas en el orden del CSV.
3. **Los timestamps están en UTC** (`2026-04-13 06:11:07.000+0000`). cqlsh muestra los timestamps en UTC, así que una entrada a las 08:11 en Madrid se verá como 06:11: es lo esperado. Las columnas `fecha` y `hora` sí están en hora local.
4. **Cassandra no avisa de duplicados:** si dos filas comparten clave primaria, la segunda sobrescribe a la primera. Las claves usadas en las tablas son únicas en estos datos.
5. **`accesos.csv` pesa unos 7 MB**, y COPY lo carga en pocos segundos. Si Cassandra corre en Docker, el fichero tiene que estar dentro del contenedor (copiándolo o montando un volumen).

## Supuestos de la simulación

Os pueden servir para la justificación del contexto en la memoria.

- **Salas:** 3 campus (Móstoles, Fuenlabrada y Vicálvaro) con 11 salas y 732 puestos. Hay de 40 a 120 puestos por sala.
- **Calendario:**
  - Clases del 13 de abril al 8 de mayo.
  - Repaso del 11 al 22 de mayo.
  - Exámenes del 23 de mayo al 12 de junio.
  - Entre convocatorias del 15 al 19 de junio.
  - Extraordinaria del 22 al 26 de junio.
- **Días cerrados:** domingos, el 1 de mayo en todos los campus y el 15 de mayo en Vicálvaro (San Isidro, festivo local de Madrid).
- **Sábados:** el 23 y el 30 de mayo y el 6 de junio abren las salas de biblioteca, de 9:00 a 14:00.
- **Horario ampliado:** `MOS-AUL-HA` cierra a las 23:30 durante los exámenes en lugar de a las 21:00.
- **Perfiles de estudiante:** de mañana, de tarde, de todo el día y de visitas cortas entre clases. La curva diaria muestra la subida al abrir, el bajón de la comida (14:00–15:00) y la tarde.
- **Puestos preferidos:** los que tienen enchufe y los que están junto a la ventana. Los puestos con enchufe acumulan un 30 % más de usos.
- **Salas llenas:** se registra un rechazo y el 75 % de los rechazados acepta otra sala del mismo campus con sitio, que es justo lo que haría vuestra app. El resto se marcha.

### Cifras por periodo (medias por sala y día)

| Periodo | Pico de ocupación | Ocupación media | Rechazos por sala y día |
|---|---:|---:|---:|
| Clases | 61,6 % | 35,6 % | 0,0 |
| Repaso | 73,8 % | 43,0 % | 0,6 |
| Exámenes | 99,2 % | 74,7 % | 30,6 |
| Entre convocatorias | 50,9 % | 34,6 % | 0,0 |
| Extraordinaria | 65,7 % | 46,4 % | 0,0 |

En total hay 5.763 rechazos y 2.099 accesos redirigidos.

## Validación realizada

Se ha comprobado automáticamente que:

- ningún puesto tiene dos ocupantes a la vez;
- ningún estudiante está en dos salas a la vez;
- la ocupación nunca supera la capacidad;
- no hay accesos fuera de horario ni en días cerrados;
- todas las referencias (estudiante, sala, puesto) existen en los catálogos;
- los ficheros derivados coinciden con el recálculo desde `accesos.csv`;
- las claves primarias del plan son únicas;
- los formatos de fecha, hora, timestamp y booleano son los que acepta cqlsh.