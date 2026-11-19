
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import get_current_user
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import login
from app.schemas.auth import RefreshRequest
from app.services.auth_service import refresh_session, logout_session

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Autenticación"]
)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK
)
def iniciar_sesion(data: LoginRequest):
    return login(
        correo=data.correo,
        password=data.password
    )


@router.get("/me")
def obtener_usuario_actual(
    current_user: dict = Depends(get_current_user)
):
    return {
        "id_usuario": current_user["id_usuario"],
        "nombre": current_user["nombre"],
        "apellidos": current_user["apellidos"],
        "correo": current_user["correo"],
        "roles": current_user["roles"],
        "permisos_globales": sorted(
            current_user["permisos_globales"]
        ),
        "permisos_por_empresa": {
            empresa: sorted(permisos)
            for empresa, permisos in
            current_user["permisos_por_empresa"].items()
        }
    }

@router.post(
    "/refresh",
    response_model=TokenResponse
)
def renovar_sesion(data: RefreshRequest):
    return refresh_session(data.refresh_token)


@router.post("/logout")
def cerrar_sesion(data: RefreshRequest):
    revoked = logout_session(data.refresh_token)

    return {
        "mensaje": (
            "Sesión cerrada correctamente"
            if revoked
            else "La sesión ya no existe o fue revocada"
        )
    }
