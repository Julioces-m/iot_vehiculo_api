
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
    9: "LUZ",
    10: "SONIDO",
    11: "DETENER",
}


@router.websocket("/ws/vehiculos/{vehiculo_id}")
async def websocket_endpoint(websocket: WebSocket, vehiculo_id: int):

    # Registrar conexión WebSocket
    await ws_manager.connect(websocket, vehiculo_id)

    # Consultar y actualizar estado inicial
    try:
        with DatabaseManager.get_connection() as conn:
            repo = StoredProcedureRepository(conn)

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
        logger.exception(
            "Error al inicializar WebSocket del vehículo %s",
            vehiculo_id,
        )

        try:
            await websocket.send_json({
                "tipo_evento": "error",
                "mensaje": str(e),
            })
        except Exception:
            pass

    # Recibir comandos
    try:
        while True:

            data = await websocket.receive_text()

            if data.isdigit():

                comando_num = int(data)

                nombre_comando = NOMBRES_COMANDOS.get(
                    comando_num,
                    "DESCONOCIDO",
                )

                logger.info(
                    "Vehículo %s recibió comando %s: %s",
                    vehiculo_id,
                    comando_num,
                    nombre_comando,
                )

                try:
                    with DatabaseManager.get_connection() as conn:

                        repo = StoredProcedureRepository(conn)

                        # Buscar el comando en el catálogo de MySQL
                        comandos = repo.sp_obtener_comandos_vehiculo(
                            vehiculo_id
                        )

                        comando_db = next(
                            (
                                c for c in comandos
                                if int(c["codigo"]) == comando_num
                                and int(c.get("activo", 1)) == 1
                            ),
                            None,
                        )

                        if not comando_db:
                            logger.warning(
                                "El código %s no existe o está inactivo "
                                "para el vehículo %s",
                                comando_num,
                                vehiculo_id,
                            )
                            continue

                        # Obtener el identificador real de MySQL
                        id_comando = comando_db["id_comando"]
                        nombre_comando = comando_db["nombre"]

                        # Actualizar estado del vehículo
                        repo.sp_actualizar_estado(
                            id_vehiculo=vehiculo_id,
                            id_comando=id_comando,
                            conectado=True,
                        )

                        # Registrar movimiento en historial
                        repo.sp_registrar_historial(
                            id_vehiculo=vehiculo_id,
                            id_comando=id_comando,
                            origen="WebSocket",
                        )

                        conn.commit()

                    # Notificar a los clientes conectados
                    evento = {
                        "tipo_evento": "movimiento_individual",
                        "vehiculo_id": vehiculo_id,
                        "id_comando": id_comando,
                        "comando": nombre_comando,
                        "codigo": comando_num,
                        "origen": "WebSocket",
                    }

                    await ws_manager.broadcast_to_vehicle(
                        vehiculo_id,
                        evento,
                    )

                except Exception as db_err:
                    logger.exception(
                        "Error al registrar comando %s del vehículo %s",
                        comando_num,
                        vehiculo_id,
                    )

                    # La conexión se cierra al salir del bloque,
                    # pero se intenta revertir la transacción.
                    try:
                        conn.rollback()
                    except Exception:
                        pass

            else:
                logger.info(
                    "Mensaje recibido del vehículo %s: %s",
                    vehiculo_id,
                    data,
                )

    except WebSocketDisconnect:

        ws_manager.disconnect(websocket, vehiculo_id)

        _marcar_desconexion_db(vehiculo_id)

        logger.info(
            "Conexión WebSocket cerrada para vehículo %s",
            vehiculo_id,
        )

    except Exception:

        logger.exception(
            "Excepción en WebSocket del vehículo %s",
            vehiculo_id,
        )

        ws_manager.disconnect(websocket, vehiculo_id)

        _marcar_desconexion_db(vehiculo_id)


def _marcar_desconexion_db(vehiculo_id: int):
    """Actualizar el estado del vehículo como desconectado."""

    try:
        with DatabaseManager.get_connection() as conn:

            repo = StoredProcedureRepository(conn)

            repo.sp_actualizar_estado(
                id_vehiculo=vehiculo_id,
                id_comando=None,
                conectado=False,
            )

            conn.commit()

    except Exception:
        logger.exception(
            "Error al marcar desconexión del vehículo %s",
            vehiculo_id,
        )
