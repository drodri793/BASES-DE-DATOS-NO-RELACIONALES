# App de estudiantes (Persona 2): recibe los avisos de Redis Cloud con PSUBSCRIBE y
# calcula la latencia de cada aviso (hora de llegada - hora de envío).
import json, sys, time
from config_nube import conectar_nube

# El patrón filtra los avisos por el nombre del canal (aviso:<prioridad>:<campus>:<sala>):
#   python suscriptor_avisos.py                 -> todos los avisos
#   python suscriptor_avisos.py aviso:alta:*    -> solo prioridad alta (salas llenas)
#   python suscriptor_avisos.py aviso:*:VIC:*   -> solo el campus de Vicálvaro

def main():
    patron = sys.argv[1] if len(sys.argv) > 1 else "aviso:*"
    nube = conectar_nube("app")  # usuario de las ACL que solo lee la caché y escucha los avisos
    p = nube.pubsub()
    p.psubscribe(patron)
    print(f"[app] escuchando los canales {patron}")

    latencias = []
    for m in p.listen():
        if m["type"] != "pmessage":  # el primer mensaje solo confirma la suscripción
            continue
        aviso = json.loads(m["data"])
        latencia = time.time() * 1000 - aviso["ts"]
        latencias.append(latencia)
        media = sum(latencias) / len(latencias)
        print(f"[app] {aviso['sala']}: {aviso['nivel']} ({aviso['libres']}/{aviso['capacidad']} libres)"
              f" - latencia {latencia:.1f} ms (media {media:.1f} ms)")

if __name__ == "__main__":
    main()
