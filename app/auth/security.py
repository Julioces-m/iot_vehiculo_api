
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.config import settings


# Argon2id para contraseñas
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Genera un hash seguro de la contraseña."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica una contraseña contra su hash."""
    try:
        return password_hasher.verify(password, password_hash)
    except Exception:
        return False


def create_access_token(user_id: int, session_id: int) -> str:
    """Genera un JWT de acceso vinculado a una sesión de BD."""

    if not settings.JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY no está configurada")

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "sid": int(session_id),
        "type": "access",
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> dict:
    """Valida y decodifica un JWT de acceso."""

    if not settings.JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY no está configurada")

    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Tipo de token incorrecto")

    if not payload.get("sub"):
        raise jwt.InvalidTokenError("Token sin identificador de usuario")

    if not payload.get("sid"):
        raise jwt.InvalidTokenError("Token sin identificador de sesión")

    try:
        user_id = int(payload["sub"])
        session_id = int(payload["sid"])

        if user_id <= 0 or session_id <= 0:
            raise ValueError()

    except (ValueError, TypeError):
        raise jwt.InvalidTokenError("Identificadores de token inválidos")

    return payload


def create_refresh_token() -> str:
    """Genera un token opaco para renovar la sesión."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """Devuelve el SHA-256 del refresh token para almacenarlo en BD."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
