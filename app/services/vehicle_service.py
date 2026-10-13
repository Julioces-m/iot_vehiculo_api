from fastapi import HTTPException, status
from datetime import datetime
from app.database import DatabaseManager
from app.repositories.sp_repository import StoredProcedureRepository
from app.websocket.ws_manager import ws_manager

class VehicleService:
    @staticmethod
    async def ejecutar_movimiento_individual(vehiculo_id: int, comando_input: str, origen: str = "API"):
        with DatabaseManager.get_connection() as conn:
            repo = StoredProcedureRepository(conn)
            
            # 1. Validar existencia del vehículo
            vehiculo = repo.sp_obtener_vehiculo(vehiculo_id)
            if not vehiculo or not vehiculo.get("activo"):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado o inactivo")

            # 2. Buscar el comando por 'nombre' ("AVANZAR") o 'codigo' (1)
            comandos = repo.sp_obtener_comandos_vehiculo(vehiculo_id)
            cmd_valido = None
            for c in comandos:
                if not c.get("activo", 1):
                    continue
                if (str(c["nombre"]).upper() == str(comando_input).upper() or 
                    str(c["codigo"]) == str(comando_input) or 
                    str(c["id_comando"]) == str(comando_input)):
                    cmd_valido = c
                    break

            if not cmd_valido:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comando no válido para este vehículo")

            # 3. Transacción en RDS usando el id_comando correspondiente
            id_comando = cmd_valido["id_comando"]
            try:
                repo.sp_actualizar_estado(vehiculo_id, id_comando, conectado=True)
                repo.sp_registrar_historial(vehiculo_id, id_comando, origen)
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error en transacción: {str(e)}")

        # 4. Notificar evento a WebSocket
        event_payload = {
            "tipo_evento": "movimiento_individual",
            "vehiculo_id": vehiculo_id,
            "comando": cmd_valido["nombre"],
            "codigo": cmd_valido["codigo"],
            "origen": origen,
            "timestamp": datetime.utcnow().isoformat()
        }
        await ws_manager.broadcast_to_vehicle(vehiculo_id, event_payload)

        return {"status": "ok", "mensaje": "Movimiento registrado correctamente", "data": event_payload}

    @staticmethod
    def obtener_historial_reciente(vehiculo_id: int) -> list:
        with DatabaseManager.get_connection() as conn:
            repo = StoredProcedureRepository(conn)
            vehiculo = repo.sp_obtener_vehiculo(vehiculo_id)
            if not vehiculo:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado")
            
            # Devuelve como MÁXIMO los 10 movimientos más recientes
            historial = repo.sp_obtener_historial(vehiculo_id)
            return historial[:10]