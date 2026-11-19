
import asyncio
import logging
from datetime import datetime

from app.database import DatabaseManager
from app.repositories.sp_repository import StoredProcedureRepository
from app.websocket.ws_manager import ws_manager

logger = logging.getLogger(__name__)


class DemoExecutionManager:

    def __init__(self):
        self._running_demos: dict[int, asyncio.Task] = {}
        self._cancel_events: dict[int, asyncio.Event] = {}

    def is_running(self, vehiculo_id: int) -> bool:

        return (
            vehiculo_id in self._running_demos
            and not self._running_demos[vehiculo_id].done()
        )

    def cancel_demo(self, vehiculo_id: int) -> bool:

        if self.is_running(vehiculo_id):

            self._cancel_events[vehiculo_id].set()

            return True

        return False

    async def run_demo_task(
        self,
        vehiculo_id: int,
        demo_id: int,
        movimientos: list,
    ):

        cancel_event = asyncio.Event()

        self._cancel_events[vehiculo_id] = cancel_event

        try:

            # Notificar inicio de DEMO
            await ws_manager.broadcast_to_vehicle(
                vehiculo_id,
                {
                    "tipo_evento": "demo_inicio",
                    "vehiculo_id": vehiculo_id,
                    "demo_id": demo_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            # Ejecutar cada movimiento de la secuencia
            for mov in movimientos:

                if cancel_event.is_set():
                    break

                id_comando = mov["id_comando"]

                try:

                    with DatabaseManager.get_connection() as conn:

                        repo = StoredProcedureRepository(conn)

                        # Actualizar estado
                        repo.sp_actualizar_estado(
                            id_vehiculo=vehiculo_id,
                            id_comando=id_comando,
                            conectado=True,
                        )

                        # Registrar movimiento individual
                        repo.sp_registrar_historial(
                            id_vehiculo=vehiculo_id,
                            id_comando=id_comando,
                            origen=f"DEMO {demo_id}",
                        )

                        conn.commit()

                except Exception:

                    logger.exception(
                        "Error registrando movimiento %s de DEMO %s",
                        id_comando,
                        demo_id,
                    )

                    raise

                timestamp = datetime.utcnow().isoformat()

                # Notificar movimiento individual de DEMO
                evento = {
                    "tipo_evento": "demo_movimiento",
                    "vehiculo_id": vehiculo_id,
                    "demo_id": demo_id,
                    "id_comando": id_comando,
                    "comando": mov.get("comando"),
                    "codigo": mov.get("codigo"),
                    "orden": mov["orden"],
                    "duracion_ms": mov["duracion_ms"],
                    "pausa_ms": mov["pausa_ms"],
                    "origen": f"DEMO {demo_id}",
                    "timestamp": timestamp,
                }

                await ws_manager.broadcast_to_vehicle(
                    vehiculo_id,
                    evento,
                )

                logger.info(
                    "DEMO %s | Vehículo %s | Movimiento %s registrado",
                    demo_id,
                    vehiculo_id,
                    id_comando,
                )

                # Respetar duración del movimiento
                duracion_sec = mov["duracion_ms"] / 1000.0

                try:

                    await asyncio.wait_for(
                        cancel_event.wait(),
                        timeout=duracion_sec,
                    )

                    break

                except asyncio.TimeoutError:
                    pass

                # Respetar pausa configurada
                pausa_sec = mov["pausa_ms"] / 1000.0

                if pausa_sec > 0:

                    try:

                        await asyncio.wait_for(
                            cancel_event.wait(),
                            timeout=pausa_sec,
                        )

                        break

                    except asyncio.TimeoutError:
                        pass

            # Finalización o cancelación
            if cancel_event.is_set():

                await ws_manager.broadcast_to_vehicle(
                    vehiculo_id,
                    {
                        "tipo_evento": "demo_cancelada",
                        "vehiculo_id": vehiculo_id,
                        "demo_id": demo_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            else:

                await ws_manager.broadcast_to_vehicle(
                    vehiculo_id,
                    {
                        "tipo_evento": "demo_fin",
                        "vehiculo_id": vehiculo_id,
                        "demo_id": demo_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

        except Exception as e:

            logger.exception(
                "Error ejecutando DEMO %s del vehículo %s",
                demo_id,
                vehiculo_id,
            )

            await ws_manager.broadcast_to_vehicle(
                vehiculo_id,
                {
                    "tipo_evento": "demo_error",
                    "vehiculo_id": vehiculo_id,
                    "demo_id": demo_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        finally:

            self._running_demos.pop(vehiculo_id, None)

            self._cancel_events.pop(vehiculo_id, None)

    def start_demo(
        self,
        vehiculo_id: int,
        demo_id: int,
        movimientos: list,
    ):

        task = asyncio.create_task(
            self.run_demo_task(
                vehiculo_id,
                demo_id,
                movimientos,
            )
        )

        self._running_demos[vehiculo_id] = task


demo_manager = DemoExecutionManager()
