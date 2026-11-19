# Conexión con Redis Cloud (segundo despliegue) y nombres de los canales de la nube.

import os
import redis

# Las credenciales no van en el código: se leen del fichero .env de esta carpeta
RUTA_ENV = os.path.join(os.path.dirname(__file__), ".env")

def leer_env():
    # Lee las líneas CLAVE=valor del .env y las guarda en un diccionario
    datos = {}
    for linea in open(RUTA_ENV, encoding="utf-8-sig"):  # utf-8-sig: por si el Bloc de notas añade un BOM
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            clave, valor = linea.split("=", 1)
            datos[clave] = valor
    return datos

def conectar_nube(usuario="default"):
    # Cada usuario de las ACL tiene su contraseña en el .env: "backend" -> REDIS_CLOUD_PASSWORD_BACKEND,
    # "app" -> REDIS_CLOUD_PASSWORD_APP... El usuario "default" usa REDIS_CLOUD_PASSWORD
    env = leer_env()
    if usuario == "default":
        password = env["REDIS_CLOUD_PASSWORD"]
    else:
        password = env["REDIS_CLOUD_PASSWORD_" + usuario.upper()]
    r = redis.Redis(host=env["REDIS_CLOUD_HOST"], port=int(env["REDIS_CLOUD_PORT"]),
                    username=usuario, password=password, decode_responses=True)
    r.ping()  # Igual que en config.conectar(): comprobamos que Redis Cloud responde
    return r

# Canales de Pub/Sub de la nube: aviso:<prioridad>:<campus>:<sala>
def canal_aviso(prioridad, campus, s):  return f"aviso:{prioridad}:{campus}:{s}"

# Caché del aforo en la nube: cache:aforo:<sala>, que caduca a los TTL_CACHE segundos
TTL_CACHE = 15
def cache_sala(s):  return f"cache:aforo:{s}"

if __name__ == "__main__":
    # Prueba de la conexión: escribimos una clave que caduca a los 30 segundos y la leemos
    r = conectar_nube("backend")
    r.set("cache:prueba", "conexion correcta", ex=30)
    print("Redis Cloud responde:", r.get("cache:prueba"), "- caduca en", r.ttl("cache:prueba"), "s")
