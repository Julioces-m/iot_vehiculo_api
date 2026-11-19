
from datetime import datetime, timezone

import jwt

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import DatabaseManager
from app.auth.security import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    """
    Valida el JWT, comprueba la sesión en MySQL y recupera
    los roles y permisos vigentes del usuario.
    """

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticación requerida o sesión inválida",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)

        user_id = int(payload["sub"])
        session_id = int(payload["sid"])

    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        raise unauthorized

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    with DatabaseManager.get_connection() as conn:
        with conn.cursor() as cursor:

            # 1. Comprobar que la sesión del JWT siga vigente.
            cursor.execute(
                """
                SELECT id_sesion
                FROM sesiones_usuario
                WHERE id_sesion = %s
                  AND id_usuario = %s
                  AND fecha_revocacion IS NULL
                  AND fecha_expiracion > %s
                LIMIT 1
                """,
                (session_id, user_id, now)
            )

            active_session = cursor.fetchone()

            if not active_session:
                raise unauthorized

            # 2. Recuperar usuario activo.
            cursor.execute(
                """
                SELECT
                    id_usuario,
                    nombre,
                    apellidos,
                    correo,
                    activo,
                    correo_verificado
                FROM usuarios
                WHERE id_usuario = %s
                LIMIT 1
                """,
                (user_id,)
            )

            user = cursor.fetchone()

            if not user or not user["activo"]:
                raise unauthorized

            # 3. Recuperar roles y permisos vigentes.
            cursor.execute(
                """
                SELECT
                    r.codigo AS rol,
                    r.alcance,
                    ur.id_empresa,
                    p.codigo AS permiso
                FROM usuario_roles ur
                INNER JOIN roles r
                    ON r.id_rol = ur.id_rol
                LEFT JOIN rol_permisos rp
                    ON rp.id_rol = r.id_rol
                LEFT JOIN permisos p
                    ON p.id_permiso = rp.id_permiso
                    AND p.activo = 1
                WHERE ur.id_usuario = %s
                  AND r.activo = 1
                  AND (
                    (
                        r.alcance = 'GLOBAL'
                        AND ur.id_empresa IS NULL
                    )
                    OR
                    (
                        r.alcance = 'EMPRESA'
                        AND ur.id_empresa IS NOT NULL
                        AND EXISTS (
                            SELECT 1
                            FROM usuario_empresa ue
                            INNER JOIN empresas e
                                ON e.id_empresa = ue.id_empresa
                            WHERE ue.id_usuario = ur.id_usuario
                              AND ue.id_empresa = ur.id_empresa
                              AND ue.activo = 1
                              AND e.activo = 1
                        )
                    )
                  )
                """,
                (user_id,)
            )

            role_rows = cursor.fetchall()

    roles = set()
    permisos_globales = set()
    permisos_por_empresa = {}

    for row in role_rows:
        roles.add(row["rol"])

        permiso = row["permiso"]

        if not permiso:
            continue

        if row["alcance"] == "GLOBAL":
            permisos_globales.add(permiso)

        elif row["alcance"] == "EMPRESA":
            empresa_id = str(row["id_empresa"])

            permisos_por_empresa.setdefault(
                empresa_id, set()
            ).add(permiso)

    return {
        **user,
        "id_sesion": session_id,
        "roles": sorted(roles),
        "permisos_globales": permisos_globales,
        "permisos_por_empresa": permisos_por_empresa
    }


def require_permission(permission_code: str):
    """
    Crea una dependencia que exige un permiso.
    Los permisos empresariales requieren X-Empresa-ID.
    """

    def permission_checker(
        current_user: dict = Depends(get_current_user),
        empresa_id: int | None = Header(
            default=None,
            alias="X-Empresa-ID"
        )
    ):
        if permission_code in current_user["permisos_globales"]:
            return current_user

        if empresa_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere el encabezado X-Empresa-ID"
            )

        permisos = current_user[
            "permisos_por_empresa"
        ].get(str(empresa_id), set())

        if permission_code not in permisos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para realizar esta operación"
            )

        return current_user

    return permission_checker
