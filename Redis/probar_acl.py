# Prueba las reglas ACL de Redis Cloud (Persona 2): con cada usuario intenta operaciones
# permitidas y prohibidas, y muestra si Redis las acepta o las rechaza con un error NOPERM.
# Código hecho con ayuda de IA (Claude): ver README, apartado "Uso de IA".
import redis
from config_nube import conectar_nube

# Para cada usuario: (qué intenta hacer, comando de Redis)
PRUEBAS = {
    "backend": [
        ("Guardar el aforo en la caché", "SET cache:aforo:PRUEBA 10 EX 60"),
        ("Publicar un aviso", "PUBLISH aviso:baja:MOS:PRUEBA prueba"),
        ("Escribir fuera de la caché", "SET sala:MOS-BIB-S1 0"),
        ("Publicar en otro canal", "PUBLISH chat:general hola"),
        ("Listar todas las claves", "KEYS *"),
    ],
    "app": [
        ("Leer el aforo de la caché", "GET cache:aforo:PRUEBA"),
        ("Suscribirse a las salas llenas", "PSUBSCRIBE aviso:alta:*"),
        ("Suscribirse a otros canales", "PSUBSCRIBE chat:*"),
        ("Cambiar el aforo de la caché", "SET cache:aforo:PRUEBA 0"),
        ("Publicar un aviso falso", "PUBLISH aviso:alta:MOS:PRUEBA falso"),
    ],
    "bibliotecario": [
        ("Publicar un aviso manual", "PUBLISH aviso:alta:MOS:MOS-BIB-S1 sala_cerrada"),
        ("Borrar una sala de la caché", "DEL cache:aforo:PRUEBA"),
        ("Inventarse el aforo de una sala", "SET cache:aforo:PRUEBA 99"),
        ("Suscribirse a los avisos", "PSUBSCRIBE aviso:*"),
    ],
    "analista": [
        ("Ver estadísticas del servidor", "INFO stats"),
        ("Leer cualquier clave", "GET cache:aforo:PRUEBA"),
        ("Escribir en la caché", "SET cache:aforo:PRUEBA 1"),
        ("Borrar una clave", "DEL cache:aforo:PRUEBA"),
        ("Publicar un aviso", "PUBLISH aviso:alta:MOS:PRUEBA prueba"),
    ],
}

def probar(r, descripcion, comando):
    try:
        if comando.startswith("PSUBSCRIBE"):
            # Las suscripciones van por su propia conexión; la respuesta (o el error) llega al leer
            p = r.pubsub()
            p.psubscribe(comando.split()[1])
            p.get_message(timeout=2)
            p.close()
        else:
            r.execute_command(*comando.split())
        resultado = "PERMITIDO"
    except redis.exceptions.NoPermissionError as e:  # error NOPERM: el usuario no tiene permiso
        resultado = f"DENEGADO  (NOPERM {e})"
    print(f"  {descripcion:34} {comando:46} {resultado}")

def main():
    for usuario, pruebas in PRUEBAS.items():
        print(f"\nUsuario {usuario}:")
        r = conectar_nube(usuario)
        for descripcion, comando in pruebas:
            probar(r, descripcion, comando)

    # El usuario por defecto debería estar desactivado
    print("\nUsuario default:")
    try:
        conectar_nube()
        print("  Sigue activo: desactívalo en Configuration > Security > Default user")
    except (redis.AuthenticationError, redis.ResponseError, KeyError) as e:
        print(f"  DESACTIVADO  ({e})")

if __name__ == "__main__":
    main()
