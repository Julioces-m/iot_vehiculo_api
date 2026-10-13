from fastapi import APIRouter, HTTPException, status
from app.database import DatabaseManager
from app.repositories.sp_repository import StoredProcedureRepository
from app.schemas.schemas import ComandoCreate, ComandoBase

router = APIRouter(prefix="/api/v1/comandos", tags=["Comandos"])

@router.post("", status_code=status.HTTP_201_CREATED)
def crear_comando(data: ComandoCreate):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        cmd_id = repo.sp_crear_comando(data.id_vehiculo, data.nombre, data.codigo, data.activo)
        conn.commit()
        return {"id": cmd_id, "mensaje": "Comando creado"}

@router.get("/vehiculo/{vehiculo_id}")
def obtener_comandos(vehiculo_id: int):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        return repo.sp_obtener_comandos_vehiculo(vehiculo_id)

@router.put("/{comando_id}")
def actualizar_comando(comando_id: int, data: ComandoBase):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        res = repo.sp_actualizar_comando(comando_id, data.nombre, data.codigo, data.activo)
        conn.commit()
        if not res:
            raise HTTPException(status_code=404, detail="Comando no encontrado")
        return {"mensaje": "Comando actualizado"}

@router.delete("/{comando_id}")
def eliminar_comando(comando_id: int):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        res = repo.sp_eliminar_comando(comando_id)
        conn.commit()
        if not res:
            raise HTTPException(status_code=404, detail="Comando no encontrado")
        return {"mensaje": "Comando eliminado"}