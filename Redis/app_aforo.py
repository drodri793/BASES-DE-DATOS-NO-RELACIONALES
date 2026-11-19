# App pública de aforo (Persona 2): consulta las plazas libres de una sala usando Redis Cloud
# como caché:
#  - Si el dato está en la caché de la nube (acierto), se devuelve directamente.
#  - Si no está (fallo), se lee del Redis local y se guarda en la nube durante TTL_CACHE segundos.

import json, random, sys, time
from config import *
from config_nube import conectar_nube, cache_sala, TTL_CACHE

def consultar(local, nube, sid):
    dato = nube.get(cache_sala(sid))
    if dato is not None:
        return json.loads(dato), "acierto"
    # Fallo de caché: leemos del Redis local y lo guardamos en la nube con caducidad
    info = local.hgetall(sala(sid))
    dato = {"sala": sid, "campus": info["campus"], "capacidad": int(info["capacidad"]),
            "libres": int(local.zscore(ZSET_LIBRES, sid))}
    nube.set(cache_sala(sid), json.dumps(dato), ex=TTL_CACHE)
    return dato, "fallo"

def una_sala(local, nube, sid):
    # Consulta una sola sala y muestra de dónde sale el dato y cuánto le queda en la caché
    if local.zscore(ZSET_LIBRES, sid) is None:
        print(f"La sala {sid} no existe")
        return
    inicio = time.perf_counter()
    dato, resultado = consultar(local, nube, sid)
    ms = (time.perf_counter() - inicio) * 1000
    print(f"{sid}: {dato['libres']}/{dato['capacidad']} libres - {resultado} ({ms:.0f} ms)"
          f" - seguirá en la caché {nube.ttl(cache_sala(sid))} s más")

def muchas_consultas(local, nube, n=200):
    # Simula a muchos estudiantes consultando salas al azar y resume los aciertos y fallos
    salas = local.zrange(ZSET_LIBRES, 0, -1)
    tiempos = {"acierto": [], "fallo": []}
    for i in range(n):
        sid = random.choice(salas)
        inicio = time.perf_counter()
        dato, resultado = consultar(local, nube, sid)
        tiempos[resultado].append((time.perf_counter() - inicio) * 1000)
        print(f"[app] {sid}: {dato['libres']} libres ({resultado})")
        time.sleep(0.1)

    aciertos, fallos = len(tiempos["acierto"]), len(tiempos["fallo"])
    print(f"\n{n} consultas: {aciertos} aciertos ({100 * aciertos / n:.0f} %) y {fallos} fallos")
    print(f"Solo {fallos} de las {n} consultas han tenido que leer del Redis local de los tornos")
    if aciertos:
        print(f"Tiempo medio de un acierto: {sum(tiempos['acierto']) / aciertos:.0f} ms")
    if fallos:
        print(f"Tiempo medio de un fallo:   {sum(tiempos['fallo']) / fallos:.0f} ms")

def main():
    local = conectar()
    nube = conectar_nube("backend")  # el servidor de la app es quien rellena la caché
    if len(sys.argv) > 1:
        una_sala(local, nube, sys.argv[1])  # python app_aforo.py VIC-BIB-S2
    else:
        muchas_consultas(local, nube)       # python app_aforo.py

if __name__ == "__main__":
    main()
