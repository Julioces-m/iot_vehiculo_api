
from getpass import getpass

from app.database import DatabaseManager
from app.auth.security import hash_password


def crear_superadmin():
    print("\n=== Inicialización del SUPERADMIN GLOBAL ===\n")

    nombre = input("Nombre: ").strip()
    apellidos = input("Apellidos: ").strip()
    correo = input("Correo electrónico: ").strip().lower()

    if not nombre or not correo:
        print("Error: nombre y correo son obligatorios.")
        return

    password = getpass("Contraseña: ")
    confirmacion = getpass("Confirmar contraseña: ")

    if password != confirmacion:
        print("Error: las contraseñas no coinciden.")
        return

    if len(password) < 12:
        print("Error: utiliza al menos 12 caracteres.")
        return

    password_hash = hash_password(password)

    with DatabaseManager.get_connection() as conn:
        try:
            with conn.cursor() as cursor:

                # Verificar que el rol global exista.
                cursor.execute(
                    """
                    SELECT id_rol
                    FROM roles
                    WHERE codigo = 'SUPERADMIN'
                      AND alcance = 'GLOBAL'
                      AND activo = 1
                    LIMIT 1
                    """
                )
                rol = cursor.fetchone()

                if not rol:
                    raise RuntimeError(
                        "No existe el rol SUPERADMIN global activo."
                    )

                # Evitar crear más de una cuenta inicial.
                cursor.execute(
                    """
                    SELECT ur.id_usuario
                    FROM usuario_roles ur
                    INNER JOIN roles r
                        ON r.id_rol = ur.id_rol
                    WHERE r.codigo = 'SUPERADMIN'
                      AND ur.id_empresa IS NULL
                    LIMIT 1
                    """
                )

                if cursor.fetchone():
                    raise RuntimeError(
                        "Ya existe un SUPERADMIN global. "
                        "No se creará otra cuenta."
                    )

                # Verificar que el correo no esté registrado.
                cursor.execute(
                    """
                    SELECT id_usuario
                    FROM usuarios
                    WHERE correo = %s
                    LIMIT 1
                    """,
                    (correo,)
                )

                if cursor.fetchone():
                    raise RuntimeError(
                        "El correo ya está registrado."
                    )

                # Crear usuario.
                cursor.execute(
                    """
                    INSERT INTO usuarios (
                        nombre,
                        apellidos,
                        correo,
                        password_hash,
                        activo,
                        correo_verificado
                    )
                    VALUES (%s, %s, %s, %s, 1, 0)
                    """,
                    (
                        nombre,
                        apellidos or None,
                        correo,
                        password_hash
                    )
                )

                user_id = cursor.lastrowid

                # Asignar rol global.
                cursor.execute(
                    """
                    INSERT INTO usuario_roles (
                        id_usuario,
                        id_rol,
                        id_empresa
                    )
                    VALUES (%s, %s, NULL)
                    """,
                    (user_id, rol["id_rol"])
                )

            conn.commit()

            print("\nSUPERADMIN creado correctamente.")
            print("ID de usuario:", user_id)
            print("Correo:", correo)
            print("Alcance: GLOBAL")

        except Exception:
            conn.rollback()
            raise


if __name__ == "__main__":
    crear_superadmin()
