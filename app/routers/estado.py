from fastapi import APIRouter, HTTPException
from app.database import DatabaseManager
from app.repositories.sp_repository import StoredProcedureRepository
from app.services.vehicle_service import VehicleService
from app.schemas.schemas import MovimientoEjecutarRequest

router = APIRouter(prefix="/api/v1/estado", tags=["Estado y Movimientos"])

@router.post("/vehiculos/{vehiculo_id}/movimiento")
async def ejecutar_movimiento(vehiculo_id: int, req: MovimientoEjecutarRequest):
    return await VehicleService.ejecutar_movimiento_individual(vehiculo_id, req.comando, req.origen)

@router.get("/vehiculos/{vehiculo_id}")
def consultar_estado(vehiculo_id: int):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        estado = repo.sp_obtener_estado(vehiculo_id)
        if not estado:
            raise HTTPException(status_code=404, detail="Estado no encontrado")
        return estado