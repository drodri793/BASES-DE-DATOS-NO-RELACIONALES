# Puente entre el Redis local y Redis Cloud (Persona 2).
# Cada medio segundo lee las plazas libres de cada sala en el Redis local y, cuando una sala
# cambia de nivel (llena, casi llena o con sitio), publica un aviso en Redis Cloud.

import json, time
from config import *
from config_nube import conectar_nube, canal_aviso, cache_sala

# Cada nivel tiene una prioridad, que va dentro del nombre del canal
PRIORIDAD = {"LLENA": "alta", "CASI_LLENA": "media", "HAY_SITIO": "baja"}

def nivel(libres, anterior):
    if libres == 0:
        return "LLENA"
    # Una sala llena no vuelve a tener sitio hasta que haya 3 plazas libres. Así no mandamos
    # un aviso cada vez que alguien entra o sale de una sala que está casi llena
    if anterior == "LLENA" and libres < 3:
        return "LLENA"
    if libres <= 5:
        return "CASI_LLENA"
    return "HAY_SITIO"

def publicar(local, nube, sid, nuevo, libres):
    info = local.hgetall(sala(sid))  # campus, nombre y capacidad de la sala
    canal = canal_aviso(PRIORIDAD[nuevo], info["campus"], sid)
    mensaje = {"sala": sid, "nivel": nuevo, "libres": libres, "capacidad": info["capacidad"],
               "ts": time.time() * 1000}  # hora de envío en ms, para calcular la latencia
    nube.publish(canal, json.dumps(mensaje))
    # La sala ha cambiado de nivel: borramos su dato de la caché para que la app no muestre uno viejo
    nube.delete(cache_sala(sid))
    print(f"[puente] {canal}: {nuevo} ({libres} libres)")

def main():
    nube = conectar_nube("backend")  # usuario de las ACL que puede escribir la caché y publicar avisos
    local = None
    estado = {}  # último nivel conocido de cada sala
    while True:
        try:
            if local is None:
                local = conectar()  # lee maestro_actual.txt: tras un failover se conecta al nuevo maestro
                print("[puente] conectado al Redis local")
            for sid, libres in local.zrange(ZSET_LIBRES, 0, -1, withscores=True):
                libres = int(libres)
                nuevo = nivel(libres, estado.get(sid))
                # En la primera lectura solo guardamos el nivel; después avisamos de cada cambio
                if sid in estado and nuevo != estado[sid]:
                    publicar(local, nube, sid, nuevo, libres)
                estado[sid] = nuevo
            time.sleep(0.5)
        except (redis.ConnectionError, redis.TimeoutError):
            # Igual que en el simulador: si se cae el maestro, esperamos y volvemos a conectar
            print("[puente] sin conexión con el Redis local. Reintentando en 2 s...")
            local = None
            time.sleep(2)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
