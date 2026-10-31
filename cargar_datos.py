# Cargaremos los csv de salas y puestos en Redis
import csv, os
from config import *

def main():
    r = conectar() # Abre la conexión con Redis
    # Primero abrimos el fichero llamado salas.csv
    with open(os.path.join(DATASET, "salas.csv"), encoding="utf-8") as f:
        salas = list(csv.DictReader(f)) # almacenamos todas las filas en salas
    # Abrimos el fichero puestos.csv
    with open(os.path.join(DATASET, "puestos.csv"), encoding="utf-8") as f:
        filas_puestos = list(csv.DictReader(f)) # almacenamos todas las filas en puestos

    pipe = r.pipeline()
    # Recorremos la variables salas que contenía todas las filas del csv
    for s in salas:
        # sid contiene el id de la sala y cap la capacidad
        sid, cap = s["sala_id"], int(s["capacidad"])

        # Proporciona por el id toda la información de la sala como su campus, el nombre, la capacidad
        # apertura, la hora de apertura, y su hora de cierre
        pipe.hset(sala(sid), mapping={
            "campus": s["campus"], 
            "nombre": s["nombre"], 
            "capacidad": cap,
            "apertura": s["hora_apertura"], 
            "cierre": s["hora_cierre"]})

        # Eliminamos rastros anteriores por si se ejecuta más veces
        pipe.delete(puestos(sid), ocup(sid), espera(sid))
        # Crea el BITMAP inicial donde todos los puestos están a cero 
        # Hacemos cap - 1 por los índices de python
        pipe.setbit(puestos(sid), cap - 1, 0)   
        # Añadir la sala al Sorted Set de libres con su capacidad máxima
        pipe.zadd(ZSET_LIBRES, {sid: cap})

    pipe.execute()

    # Puestos con enchufe/ventana: sets por sala (útil para Insight y la demo)
    pipe = r.pipeline()
    
    # Recorremos todos los puestos, para ir comprobando si cada uno de ellos tiene enchufe y ventana
    for p in filas_puestos:
        # Coprobamos si tiene enchufe ese puesto
        if p["enchufe"] == "True":
            pipe.sadd(f"sala:{p['sala_id']}:con_enchufe", int(p["puesto"]))
        
        # Comprobamos si tiene ventana ese puesto 
        if p["ventana"] == "True":
            pipe.sadd(f"sala:{p['sala_id']}:con_ventana", int(p["puesto"]))
    pipe.execute()

if __name__ == "__main__":
    main()
