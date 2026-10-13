from fastapi import APIRouter
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/api/v1/historial", tags=["Historial"])

@router.get("/vehiculos/{vehiculo_id}")
def obtener_historial_vehiculo(vehiculo_id: int):
    return VehicleService.obtener_historial_reciente(vehiculo_id)