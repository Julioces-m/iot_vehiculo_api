
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status

from app.auth.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_refresh_token
)
from app.config import settings
from app.database import DatabaseManager


def credentials_error():
    """Genera un error genérico de autenticación."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Correo o contraseña incorrectos"
    )


def login(correo: str, password: str) -> dict:
    """
    Autentica al usuario y crea una sesión.
    Bloquea temporalmente la cuenta después de cinco intentos fallidos.
    """

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    with DatabaseManager.get_connection() as conn:
        try:
            with conn.cursor() as cursor:

                # 1. Buscar usuario y bloquear su registro.
                cursor.execute(
                    """
                    SELECT
                        id_usuario,
                        correo,
                        password_hash,
                        activo,
                        intentos_fallidos,
                        bloqueado_hasta
                    FROM usuarios
                    WHERE correo = %s
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (correo.strip(),)
                )

                user = cursor.fetchone()

                if not user or not user["activo"]:
                    raise credentials_error()

                # 2. Comprobar bloqueo temporal.
                bloqueado_hasta = user["bloqueado_hasta"]

                if bloqueado_hasta and bloqueado_hasta > now:
                    raise credentials_error()

                # 3. Verificar contraseña.
                if not verify_password(
                    password,
                    user["password_hash"]
                ):
                    intentos = user["intentos_fallidos"] + 1

                    if intentos >= 5:
                        nuevo_bloqueo = now + timedelta(minutes=15)
                    else:
                        nuevo_bloqueo = None

                    cursor.execute(
                        """
                        UPDATE usuarios
                        SET intentos_fallidos = %s,
                            bloqueado_hasta = %s
                        WHERE id_usuario = %s
                        """,
                        (
                            intentos,
                            nuevo_bloqueo,
                            user["id_usuario"]
                        )
                    )

                    conn.commit()
                    raise credentials_error()

                # 4. Restablecer intentos fallidos.
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET intentos_fallidos = 0,
                        bloqueado_hasta = NULL,
                        ultimo_acceso = %s
                    WHERE id_usuario = %s
                    """,
                    (now, user["id_usuario"])
                )

                # 5. Crear refresh token y familia.
                refresh_token = create_refresh_token()
                refresh_hash = hash_refresh_token(refresh_token)
                familia_token = str(uuid4())

                fecha_expiracion = now + timedelta(
                    days=settings.REFRESH_TOKEN_EXPIRE_DAYS
                )

                # 6. Registrar sesión en MySQL.
                cursor.execute(
                    """
                    INSERT INTO sesiones_usuario (
                        id_usuario,
                        refresh_token_hash,
                        familia_token,
                        fecha_expiracion,
                        ultimo_uso
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        user["id_usuario"],
                        refresh_hash,
                        familia_token,
                        fecha_expiracion,
                        now
                    )
                )

                # Obtener ID de la sesión recién creada.
                session_id = cursor.lastrowid

                # 7. Crear access token vinculado a la sesión.
                access_token = create_access_token(
                    user["id_usuario"],
                    session_id
                )

            conn.commit()

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": (
                    settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                )
            }

        except Exception:
            conn.rollback()
            raise


def refresh_session(refresh_token: str) -> dict:
    """
    Renueva una sesión mediante rotación de refresh token.
    Detecta la reutilización de tokens revocados y revoca
    toda la familia cuando ocurre.
    """

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    token_hash = hash_refresh_token(refresh_token)

    with DatabaseManager.get_connection() as conn:
        try:
            with conn.cursor() as cursor:

                # 1. Buscar y bloquear la sesión.
                cursor.execute(
                    """
                    SELECT
                        id_sesion,
                        id_usuario,
                        familia_token,
                        fecha_expiracion,
                        fecha_revocacion
                    FROM sesiones_usuario
                    WHERE refresh_token_hash = %s
                    FOR UPDATE
                    """,
                    (token_hash,)
                )

                session = cursor.fetchone()

                if not session:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Refresh token inválido"
                    )

                family = session["familia_token"]

                # 2. Detectar reutilización de token revocado.
                if session["fecha_revocacion"] is not None:

                    cursor.execute(
                        """
                        UPDATE sesiones_usuario
                        SET fecha_revocacion = %s
                        WHERE familia_token = %s
                          AND fecha_revocacion IS NULL
                        """,
                        (now, family)
                    )

                    conn.commit()

                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Sesión revocada por reutilización de token"
                    )

                # 3. Comprobar expiración.
                if session["fecha_expiracion"] <= now:

                    cursor.execute(
                        """
                        UPDATE sesiones_usuario
                        SET fecha_revocacion = %s
                        WHERE id_sesion = %s
                        """,
                        (now, session["id_sesion"])
                    )

                    conn.commit()

                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Refresh token expirado"
                    )

                # 4. Verificar que el usuario siga activo.
                cursor.execute(
                    """
                    SELECT activo
                    FROM usuarios
                    WHERE id_usuario = %s
                    """,
                    (session["id_usuario"],)
                )

                user = cursor.fetchone()

                if not user or not user["activo"]:

                    cursor.execute(
                        """
                        UPDATE sesiones_usuario
                        SET fecha_revocacion = %s
                        WHERE familia_token = %s
                          AND fecha_revocacion IS NULL
                        """,
                        (now, family)
                    )

                    conn.commit()

                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Usuario inactivo"
                    )

                # 5. Revocar el refresh token anterior.
                cursor.execute(
                    """
                    UPDATE sesiones_usuario
                    SET fecha_revocacion = %s,
                        ultimo_uso = %s
                    WHERE id_sesion = %s
                    """,
                    (
                        now,
                        now,
                        session["id_sesion"]
                    )
                )

                # 6. Crear nuevo refresh token.
                new_refresh = create_refresh_token()
                new_hash = hash_refresh_token(new_refresh)

                expiration = now + timedelta(
                    days=settings.REFRESH_TOKEN_EXPIRE_DAYS
                )

                cursor.execute(
                    """
                    INSERT INTO sesiones_usuario (
                        id_usuario,
                        refresh_token_hash,
                        familia_token,
                        fecha_expiracion,
                        ultimo_uso
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        session["id_usuario"],
                        new_hash,
                        family,
                        expiration,
                        now
                    )
                )

                # Obtener ID de la nueva sesión.
                new_session_id = cursor.lastrowid

                # 7. Crear nuevo access token vinculado a la sesión.
                new_access = create_access_token(
                    session["id_usuario"],
                    new_session_id
                )

            conn.commit()

            return {
                "access_token": new_access,
                "refresh_token": new_refresh,
                "token_type": "bearer",
                "expires_in": (
                    settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                )
            }

        except HTTPException:
            raise

        except Exception:
            conn.rollback()
            raise


def logout_session(refresh_token: str) -> bool:
    """
    Revoca todas las sesiones pertenecientes
    a la misma familia de refresh tokens.
    """

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    token_hash = hash_refresh_token(refresh_token)

    with DatabaseManager.get_connection() as conn:
        try:
            with conn.cursor() as cursor:

                # 1. Localizar familia del refresh token.
                cursor.execute(
                    """
                    SELECT familia_token
                    FROM sesiones_usuario
                    WHERE refresh_token_hash = %s
                    FOR UPDATE
                    """,
                    (token_hash,)
                )

                session = cursor.fetchone()

                if not session:
                    return False

                # 2. Revocar todos los tokens activos de la familia.
                cursor.execute(
                    """
                    UPDATE sesiones_usuario
                    SET fecha_revocacion = %s
                    WHERE familia_token = %s
                      AND fecha_revocacion IS NULL
                    """,
                    (
                        now,
                        session["familia_token"]
                    )
                )

            conn.commit()
            return True

        except Exception:
            conn.rollback()
            raise
