# Estableceremos en este fichero la lógica de entrada y salida de las salas
from config import *

# Creamos una función de como actualizar cuantos huecos libres hay
def _actualizar_libres(r, sid):
    # Leemos del hash cuál es la capacidad total de la sala mediante el comando hget
    capacidad_total = int(r.hget(sala(sid), "capacidad"))
    # Obtenemos cuantos puestos libres tenemos restando a la capacidad total cuantos puestos tienen el bit a 1 (ocupados)
    libres = capacidad_total - r.bitcount(puestos(sid))
    # Añadimos al conjunto ordenado las salas libres
    r.zadd(ZSET_LIBRES, {sid: libres})
    return libres

# Esta función nos devuelve el puesto asignado al alumno, si está ya dentro en una sala
# o None en caso de si la sala ya está llena y por ello iría a la sala de espera
def entrar(r, sid, est_id):

    # Si el alumno ya está dentro devolvemos "DENTRO"
    if not r.set(estudiante(est_id), "pendiente", nx=True):
        return "DENTRO"

    capacidad = int(r.hget(sala(sid), "capacidad")) # Cogemos el valor de la capacidad de la sala
    while True:
        # Buscamos el primer asiento que tiene una posición libre
        pos = r.bitpos(puestos(sid), 0) 

        # Comprobamos si hay sitio o si la sala está llena
        if pos == -1 or pos >= capacidad:
            r.delete(estudiante(est_id))
            r.rpush(espera(sid), est_id)
            _actualizar_libres(r, sid)
            return None

        # SETBIT devuelve el valor anterior: si era 1, otro cliente se nos adelantó -> reintentar
        if r.setbit(puestos(sid), pos, 1) == 0:
            puesto = pos + 1
            r.hset(ocup(sid), puesto, est_id)
            r.set(estudiante(est_id), f"{sid}|{puesto}")
            _actualizar_libres(r, sid)
            return puesto

# Creamos una función cuando un alumno decide salir de una sala donde se libera un puesto cuando decide
# salir y si hubiera lista de espera se le asigna ese hueco libre al primero de la lista
def salir(r, sid, puesto):
    # Con la variable estado_asiento comprobamos si el asiento ya estaba ocupado o no, y mientras lo consultamos
    # lo establece a libre
    estado_asiento =  r.setbit(puestos(sid), puesto - 1, 0)
    if estado_asiento == 0: # Es decir ya estaba libre el asiento
        return False

    # Cogemos el valor de que estudiante está ocupando el puesto
    estudiante_actual = r.hget(ocup(sid), puesto)
    # Eliminamos al estudiante como ocupante de la sala
    r.hdel(ocup(sid), puesto)

    # Eliminamos al estudiante que acaba de salir de la sala ya que un estudiante como no puede estar en dos salas
    # a la vez, al liberarle ya le permitimos estar en otra sala
    if estudiante_actual:
        r.delete(estudiante(estudiante_actual))

    _actualizar_libres(r, sid) # Actualizamos las plazas libres

    # Sacamos el siguiente de la lista de espera para que pueda entrar en la sala
    siguiente_estudiante = r.lpop(espera(sid)) # Almacenamos el nombre del siguiente estudiante
    if siguiente_estudiante:
        entrar(r, sid, siguiente_estudiante)

    return True
