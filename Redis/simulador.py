# Hace como un simulador de tornos de entradas y salidas aleatorias en todas las salas
import argparse, random, time
import redis
from config import *
from aforo import entrar, salir

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host"); ap.add_argument("--port", type=int)
    ap.add_argument("--pausa", type=float, default=0.2)
    ap.add_argument("--prob-entrada", type=float, default=0.6)
    a = ap.parse_args()
    r, n = None, 0

    while True:
        try:
            # Si la conexión con redis es la primera vez que se establece o se cae dicha conexión
            if r is None:
                # Llamamos a la función conectar para enlazar con el servidor de Redis actual
                r = conectar(a.host if n == 0 else None, a.port if n == 0 else None)
                print(f"[sim] conectado a {r.connection_pool.connection_kwargs['host']}:"
                      f"{r.connection_pool.connection_kwargs['port']}")
                
            # Elige una sala al azar de esa lista para simular lo que ocurre en ella 
            sala = random.choice(r.zrange(ZSET_LIBRES, 0, -1))
            if random.random() < a.prob_entrada:
                est = f"EST{random.randint(1, 2380):05d}"
                res = entrar(r, sala, est)
                if res not in ("DENTRO",):
                    print(f"[sim] {est} -> {sala}: " + (f"puesto {res}" if res else "SALA LLENA (espera)"))
            # En caso de que el número aleatorio no cumplió con la probabilidad de entrada, toca la salida
            else:
                ocupados = r.hkeys(ocup(sala))
                if ocupados:
                    p = int(random.choice(ocupados))
                    salir(r, sala, p)
                    print(f"[sim] sale puesto {p} de {sala}")
            time.sleep(a.pausa)
        except (redis.ConnectionError, redis.TimeoutError, redis.ReadOnlyError) as e:
            print(f"[sim] sin maestro ({type(e).__name__}). Reintentando en 2 s...")
            r, n = None, n + 1
            time.sleep(2)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
