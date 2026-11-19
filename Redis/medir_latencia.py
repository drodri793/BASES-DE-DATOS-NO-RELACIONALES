# Mide la latencia del Redis local (Docker) y de Redis Cloud para justificar el rol de cada despliegue.
# Persona 2. Código hecho con ayuda de IA (Claude): ver README, apartado "Uso de IA".
import time
from config import conectar
from config_nube import conectar_nube

N = 200  # repeticiones de cada operación

def medir(r):
    # Hacemos N veces un PING y una escritura + lectura, y guardamos lo que tarda cada una en ms
    pings, escrituras = [], []
    for i in range(N):
        t0 = time.perf_counter()
        r.ping()
        t1 = time.perf_counter()
        r.set("cache:prueba", i)
        r.get("cache:prueba")
        t2 = time.perf_counter()
        pings.append((t1 - t0) * 1000)
        escrituras.append((t2 - t1) * 1000)
    r.delete("cache:prueba")
    return sorted(pings), sorted(escrituras)

def mostrar(nombre, tiempos):
    # Al estar ordenados: el primero es el mínimo, el del medio la mediana y el último el máximo
    print(f"{nombre:28} mínimo {tiempos[0]:7.2f} ms   mediana {tiempos[N // 2]:7.2f} ms   máximo {tiempos[-1]:7.2f} ms")

def main():
    ping_local, escr_local = medir(conectar())
    ping_nube, escr_nube = medir(conectar_nube("backend"))
    mostrar("Local - PING", ping_local)
    mostrar("Local - escritura+lectura", escr_local)
    mostrar("Nube - PING", ping_nube)
    mostrar("Nube - escritura+lectura", escr_nube)
    print(f"Un PING a Redis Cloud tarda unas {ping_nube[N // 2] / ping_local[N // 2]:.0f} veces más que al Redis local")

if __name__ == "__main__":
    main()
