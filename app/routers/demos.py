from fastapi import APIRouter, HTTPException, status
from app.database import DatabaseManager
from app.repositories.sp_repository import StoredProcedureRepository
from app.schemas.schemas import DemoBase, MovimientoDemoCreate
from app.services.demo_runner import demo_manager

router = APIRouter(prefix="/api/v1/demos", tags=["DEMO"])

@router.post("", status_code=status.HTTP_201_CREATED)
def crear_demo(data: DemoBase):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        d_id = repo.sp_crear_demo(data.id_vehiculo, data.nombre, data.descripcion)
        conn.commit()
        return {"id_demo": d_id, "mensaje": "Demo creada"}

@router.get("/vehiculo/{vehiculo_id}")
def obtener_demos(vehiculo_id: int):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        return repo.sp_obtener_demos(vehiculo_id)

@router.put("/{demo_id}")
def actualizar_demo(demo_id: int, nombre: str, descripcion: str, activa: bool):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        res = repo.sp_actualizar_demo(demo_id, nombre, descripcion, activa)
        conn.commit()
        if not res:
            raise HTTPException(status_code=404, detail="Demo no encontrada")
        return {"mensaje": "Demo actualizada"}

@router.delete("/{demo_id}")
def eliminar_demo(demo_id: int):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        res = repo.sp_eliminar_demo(demo_id)
        conn.commit()
        if not res:
            raise HTTPException(status_code=404, detail="Demo no encontrada")
        return {"mensaje": "Demo eliminada"}

# --- MOVIMIENTOS DEMO ---
@router.post("/{demo_id}/movimientos", status_code=status.HTTP_201_CREATED)
def agregar_movimiento_demo(demo_id: int, data: MovimientoDemoCreate):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        m_id = repo.sp_agregar_movimiento_demo(demo_id, data.id_comando, data.orden, data.duracion_ms, data.pausa_ms)
        conn.commit()
        return {"id_demo_movimiento": m_id, "mensaje": "Movimiento de DEMO agregado"}

@router.get("/{demo_id}/movimientos")
def obtener_movimientos_demo(demo_id: int):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        return repo.sp_obtener_movimientos_demo(demo_id)

@router.put("/movimientos/{movimiento_id}")
def actualizar_movimiento_demo(movimiento_id: int, id_comando: int, orden: int, duracion_ms: int, pausa_ms: int):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        res = repo.sp_actualizar_movimiento_demo(movimiento_id, id_comando, orden, duracion_ms, pausa_ms)
        conn.commit()
        if not res:
            raise HTTPException(status_code=404, detail="Movimiento no encontrado")
        return {"mensaje": "Movimiento actualizado"}

@router.delete("/movimientos/{movimiento_id}")
def eliminar_movimiento_demo(movimiento_id: int):
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        res = repo.sp_eliminar_movimiento_demo(movimiento_id)
        conn.commit()
        if not res:
            raise HTTPException(status_code=404, detail="Movimiento eliminado")
        return {"mensaje": "Movimiento eliminado"}

# --- EJECUCIÓN Y CANCELACIÓN ---
@router.post("/{demo_id}/ejecutar")
async def ejecutar_demo(demo_id: int):  # <--- Agregado 'async' aquí
    with DatabaseManager.get_connection() as conn:
        repo = StoredProcedureRepository(conn)
        
        movimientos = repo.sp_obtener_movimientos_demo(demo_id)
        if not movimientos:
            raise HTTPException(status_code=400, detail="La DEMO no contiene movimientos o no existe")

        vehiculos = repo.sp_obtener_vehiculos()
        target_demo = None
        for v in vehiculos:
            demos = repo.sp_obtener_demos(v["id_vehiculo"])
            found = next((d for d in demos if d["id_demo"] == demo_id), None)
            if found:
                target_demo = found
                break

        if not target_demo or not target_demo.get("activo", 1):
            raise HTTPException(status_code=400, detail="DEMO inactiva o inexistente")
        
        vehiculo_id = target_demo["id_vehiculo"]

    if demo_manager.is_running(vehiculo_id):
        raise HTTPException(status_code=409, detail="Ya existe una DEMO en ejecución para este vehículo")

    demo_manager.start_demo(vehiculo_id, demo_id, movimientos)
    return {"status": "en_proceso", "mensaje": f"DEMO {demo_id} iniciada para vehículo {vehiculo_id}"}

@router.post("/vehiculo/{vehiculo_id}/cancelar")
def cancelar_demo(vehiculo_id: int):
    exito = demo_manager.cancel_demo(vehiculo_id)
    if not exito:
        raise HTTPException(status_code=400, detail="No hay ninguna DEMO en ejecución para este vehículo")
    return {"status": "cancelada", "mensaje": f"DEMO detenida para el vehículo {vehiculo_id}"}