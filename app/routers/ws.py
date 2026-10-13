from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.ws_manager import ws_manager
from app.database import DatabaseManager
from app.repositories.sp_repository import StoredProcedureRepository

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/vehiculos/{vehiculo_id}")
async def websocket_endpoint(websocket: WebSocket, vehiculo_id: int):
    await ws_manager.connect(websocket, vehiculo_id)
    
    # Al abrir conexión, enviar último estado de RDS
    try:
        with DatabaseManager.get_connection() as conn:
            repo = StoredProcedureRepository(conn)
            estado = repo.sp_obtener_estado(vehiculo_id)
            if estado:
                await websocket.send_json({
                    "tipo_evento": "conexion_inicial",
                    "vehiculo_id": vehiculo_id,
                    "estado": estado
                })
    except Exception as e:
        await websocket.send_json({"tipo_evento": "error", "mensaje": str(e)})

    try:
        while True:
            # Mantiene viva la conexión
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, vehiculo_id)