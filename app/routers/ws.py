import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.database import DatabaseManager
from app.repositories.sp_repository import StoredProcedureRepository
from app.websocket.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

NOMBRES_COMANDOS = {
    1: "AVANZAR",
    2: "RETROCEDER",
    3: "GIRAR_IZQUIERDA",
    4: "GIRAR_DERECHA",
    5: "SUBIR_BRAZO",
    6: "BAJAR_BRAZO",
    7: "ABRIR_PALA",
    8: "CERRAR_PALA",
    9: "DETENER",
}


@router.websocket("/ws/vehiculos/{vehiculo_id}")
async def websocket_endpoint(websocket: WebSocket, vehiculo_id: int):
    # Registrar la conexión en el ws_manager
    await ws_manager.connect(websocket, vehiculo_id)

    # Registrar conexión en DB y enviar estado actual desde RDS
    try:
        with DatabaseManager.get_connection() as conn:
            repo = StoredProcedureRepository(conn)

            # Marcar el vehículo como conectado en la BD (conectado = True)
            if hasattr(repo, "sp_actualizar_estado"):
                repo.sp_actualizar_estado(
                    id_vehiculo=vehiculo_id,
                    id_comando=None,
                    conectado=True,
                )
                conn.commit()

            estado = repo.sp_obtener_estado(vehiculo_id)
            if estado:
                await websocket.send_json({
                    "tipo_evento": "conexion_inicial",
                    "vehiculo_id": vehiculo_id,
                    "estado": estado,
                })
    except Exception as e:
        logger.error(
            f"Error al obtener/actualizar estado inicial del vehículo {vehiculo_id}: {e}"
        )
        try:
            await websocket.send_json(
                {"tipo_evento": "error", "mensaje": str(e)}
            )
        except Exception:
            pass

    # Mantener el canal abierto y procesar los mensajes entrantes (ESP32 o Cliente)
    try:
        while True:
            data = await websocket.receive_text()

            # Procesar comandos numéricos recibidos (del 1 al 9)
            if data.isdigit():
                comando_num = int(data)
                nombre_comando = NOMBRES_COMANDOS.get(
                    comando_num, "DESCONOCIDO"
                )
                logger.info(
                    f"Vehículo {vehiculo_id} ejecutó comando [{comando_num}: {nombre_comando}]"
                )

                # Actualizar último comando activo en la BD
                try:
                    with DatabaseManager.get_connection() as conn:
                        repo = StoredProcedureRepository(conn)
                        if hasattr(repo, "sp_actualizar_estado"):
                            repo.sp_actualizar_estado(
                                id_vehiculo=vehiculo_id,
                                id_comando=comando_num,
                                conectado=True,
                            )
                            conn.commit()
                except Exception as db_err:
                    logger.error(
                        f"Error al actualizar comando en DB para el vehículo {vehiculo_id}: {db_err}"
                    )
            else:
                logger.info(
                    f"Mensaje recibido del vehículo {vehiculo_id}: {data}"
                )

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, vehiculo_id)
        _marcar_desconexion_db(vehiculo_id)
        logger.info(
            f"Conexión WebSocket cerrada para el vehículo {vehiculo_id}"
        )
    except Exception as e:
        logger.error(
            f"Excepción en conexión WebSocket del vehículo {vehiculo_id}: {e}"
        )
        ws_manager.disconnect(websocket, vehiculo_id)
        _marcar_desconexion_db(vehiculo_id)


def _marcar_desconexion_db(vehiculo_id: int):
    """Auxiliar para actualizar estado a desconectado (conectado = False) en RDS."""
    try:
        with DatabaseManager.get_connection() as conn:
            repo = StoredProcedureRepository(conn)
            if hasattr(repo, "sp_actualizar_estado"):
                repo.sp_actualizar_estado(
                    id_vehiculo=vehiculo_id,
                    id_comando=None,
                    conectado=False,
                )
                conn.commit()
    except Exception as e:
        logger.error(
            f"Error al marcar desconexión en DB para el vehículo {vehiculo_id}: {e}"
        )