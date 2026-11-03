"""Demuestra: escribir en maestro, WAIT, leer desde réplicas y error READONLY al escribir en una réplica."""
import time, redis
from config import *

M, R1, R2 = ("localhost", 6379), ("localhost", 6380), ("localhost", 6381)

def cli(t): return redis.Redis(host=t[0], port=t[1], decode_responses=True)

def main():
    m, r1, r2 = cli(M), cli(R1), cli(R2)
    sala = "MOS-BIB-S1"
    clave = "demo:replicacion:" + sala
    print("ROLE maestro :", m.execute_command("ROLE")[0])
    for nombre, r in (("réplica 1", r1), ("réplica 2", r2)):
        print(f"ROLE {nombre}:", r.execute_command("ROLE")[0])

    for puesto in (1, 2, 5, 9):
        m.setbit(clave, puesto - 1, 1)
    ack = m.wait(2, 1500)
    print(f"WAIT -> {ack} réplicas confirmaron la escritura")

    for nombre, r in (("réplica 1", r1), ("réplica 2", r2)):
        print(f"[{nombre}] BITCOUNT={r.bitcount(clave)} puesto5={r.getbit(clave, 4)} puesto7={r.getbit(clave, 6)}")

    try:
        r1.setbit(clave, 20, 1)
    except redis.ReadOnlyError as e:
        print("Escritura en réplica rechazada (esperado):", e)
    m.delete(clave)

if __name__ == "__main__":
    main()
