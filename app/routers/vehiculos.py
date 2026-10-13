from fastapi import APIRouter, HTTPException, status
from app.database import DatabaseManager
from app.repositories.sp_repository import StoredProcedureRepository
from app.schemas.schemas import VehiculoCreate

router = APIRouter(prefix="/api/v1/vehiculos", tags=["Vehículos"])

@router.post("", status_code=status.HTTP_201_CREATED)
def crear_vehiculo(data: VehiculoCreate):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        new_id = repo.sp_crear_vehiculo(data.nombre, data.modelo, data.activo)
        conn.commit()
        return {"id": new_id, "mensaje": "Vehículo creado"}

@router.get("")
def listar_vehiculos():
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        return repo.sp_obtener_vehiculos()

@router.get("/{vehiculo_id}")
def obtener_vehiculo(vehiculo_id: int):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        v = repo.sp_obtener_vehiculo(vehiculo_id)
        if not v:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado")
        v["comandos"] = repo.sp_obtener_comandos_vehiculo(vehiculo_id)
        v["estado"] = repo.sp_obtener_estado(vehiculo_id)
        v["demos"] = repo.sp_obtener_demos(vehiculo_id)
        return v

@router.put("/{vehiculo_id}")
def actualizar_vehiculo(vehiculo_id: int, data: VehiculoCreate):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        res = repo.sp_actualizar_vehiculo(vehiculo_id, data.nombre, data.modelo, data.activo)
        conn.commit()
        if not res:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado")
        return {"mensaje": "Vehículo actualizado"}

@router.delete("/{vehiculo_id}")
def eliminar_vehiculo(vehiculo_id: int):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        res = repo.sp_eliminar_vehiculo(vehiculo_id)
        conn.commit()
        if not res:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado")
        return {"mensaje": "Vehículo eliminado"}