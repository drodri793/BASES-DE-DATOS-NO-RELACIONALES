# Establecremos la configuración común y nombres de claves 
import os
import redis

# Destino configurable: variables de entorno o fichero maestro_actual.txt ("host:puerto").
# Al hacer el failover basta con editar ese fichero: el simulador se reconecta solo.
FICHERO_DESTINO = os.path.join(os.path.dirname(__file__), "maestro_actual.txt")
DATASET = os.environ.get("DATASET_DIR", "../dataset_aforo")

def destino():
    if os.path.exists(FICHERO_DESTINO):
        txt = open(FICHERO_DESTINO).read().strip()
        if txt:
            host, port = txt.split(":")
            return host, int(port)
    # En caso de que no haya fichero o se encuentre vacío, vamos al maestro habitual.
    return os.environ.get("REDIS_HOST", "localhost"), int(os.environ.get("REDIS_PORT", 6379))

def conectar(host=None, port=None):
    # Buscamos a que destino tenemos que ir 
    h, p = destino()
    # Creamos el cliente Redis
    r = redis.Redis(host=host or h, port=port or p, decode_responses=True,
                    socket_connect_timeout=2, socket_timeout=3)
    # Hacemos un ping para comprobar que Redis no está caído
    r.ping()
    return r # Devolvemos el cliente listo para usar

# Establecemos el esquema de llaves
# ZSET_LIBRES: es una lista de elementos donde Redis almacena elementos únicos con
# cuantos puestos libres le quedan por cada sala en este caso

ZSET_LIBRES = "aforo:libres"                              # ZSET: miembro=sala_id, score=puestos libres
def sala(s):      return f"sala:{s}"              # HASH: campus, nombre, capacidad, apertura, cierre
def puestos(s):   return f"sala:{s}:puestos"      # BITMAP: ya que por ejemplo si está ocupado un puesto bit -> 1
def ocup(s):      return f"sala:{s}:ocupantes"    # HASH: nos indica que estudiante está ocupando el puesto
def espera(s):    return f"sala:{s}:espera"       # LIST: nos indica la lista de estudiantes que está esperando a entrar
def estudiante(e):        return f"estudiante:{e}:actual" # STRING: indica el lugar "sala|puesto" para evitar estar en 2 salas
