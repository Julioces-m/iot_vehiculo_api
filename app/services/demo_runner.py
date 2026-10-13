import asyncio
from datetime import datetime
from app.database import DatabaseManager
from app.repositories.sp_repository import StoredProcedureRepository
from app.websocket.ws_manager import ws_manager

class DemoExecutionManager:
    def __init__(self):
        self._running_demos: dict[int, asyncio.Task] = {}
        self._cancel_events: dict[int, asyncio.Event] = {}

    def is_running(self, vehiculo_id: int) -> bool:
        return vehiculo_id in self._running_demos and not self._running_demos[vehiculo_id].done()

    def cancel_demo(self, vehiculo_id: int) -> bool:
        if self.is_running(vehiculo_id):
            self._cancel_events[vehiculo_id].set()
            return True
        return False

    async def run_demo_task(self, vehiculo_id: int, demo_id: int, movimientos: list):
        cancel_event = asyncio.Event()
        self._cancel_events[vehiculo_id] = cancel_event

        try:
            # Evento Inicio por WebSocket
            await ws_manager.broadcast_to_vehicle(vehiculo_id, {
                "tipo_evento": "demo_inicio",
                "vehiculo_id": vehiculo_id,
                "demo_id": demo_id,
                "timestamp": datetime.utcnow().isoformat()
            })

            for mov in movimientos:
                if cancel_event.is_set():
                    break

                # Actualizar estado en RDS con id_comando (sin registrar historial)
                with DatabaseManager.get_connection() as conn:
                    repo = StoredProcedureRepository(conn)
                    repo.sp_actualizar_estado(
                        id_vehiculo=vehiculo_id,
                        id_comando=mov["id_comando"],
                        conectado=True
                    )
                    conn.commit()

                # Notificar movimiento individual de la DEMO por WebSocket
                await ws_manager.broadcast_to_vehicle(vehiculo_id, {
                    "tipo_evento": "demo_movimiento",
                    "vehiculo_id": vehiculo_id,
                    "demo_id": demo_id,
                    "comando": mov.get("comando"),
                    "codigo": mov.get("codigo"),
                    "orden": mov["orden"],
                    "duracion_ms": mov["duracion_ms"],
                    "pausa_ms": mov["pausa_ms"],
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Respetar duración
                duracion_sec = mov["duracion_ms"] / 1000.0
                try:
                    await asyncio.wait_for(cancel_event.wait(), timeout=duracion_sec)
                    break
                except asyncio.TimeoutError:
                    pass

                # Respetar pausa
                pausa_sec = mov["pausa_ms"] / 1000.0
                if pausa_sec > 0:
                    try:
                        await asyncio.wait_for(cancel_event.wait(), timeout=pausa_sec)
                        break
                    except asyncio.TimeoutError:
                        pass

            if cancel_event.is_set():
                await ws_manager.broadcast_to_vehicle(vehiculo_id, {
                    "tipo_evento": "demo_cancelada",
                    "vehiculo_id": vehiculo_id,
                    "demo_id": demo_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                await ws_manager.broadcast_to_vehicle(vehiculo_id, {
                    "tipo_evento": "demo_fin",
                    "vehiculo_id": vehiculo_id,
                    "demo_id": demo_id,
                    "timestamp": datetime.utcnow().isoformat()
                })

        except Exception as e:
            await ws_manager.broadcast_to_vehicle(vehiculo_id, {
                "tipo_evento": "demo_error",
                "vehiculo_id": vehiculo_id,
                "demo_id": demo_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        finally:
            self._running_demos.pop(vehiculo_id, None)
            self._cancel_events.pop(vehiculo_id, None)

    def start_demo(self, vehiculo_id: int, demo_id: int, movimientos: list):
        task = asyncio.create_task(self.run_demo_task(vehiculo_id, demo_id, movimientos))
        self._running_demos[vehiculo_id] = task

demo_manager = DemoExecutionManager()