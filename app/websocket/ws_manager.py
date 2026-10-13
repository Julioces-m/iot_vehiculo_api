import asyncio
from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Mapea id_vehiculo -> Lista de conexiones WebSocket activas
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, vehiculo_id: int):
        await websocket.accept()
        if vehiculo_id not in self.active_connections:
            self.active_connections[vehiculo_id] = []
        self.active_connections[vehiculo_id].append(websocket)

    def disconnect(self, websocket: WebSocket, vehiculo_id: int):
        if vehiculo_id in self.active_connections:
            if websocket in self.active_connections[vehiculo_id]:
                self.active_connections[vehiculo_id].remove(websocket)
            if not self.active_connections[vehiculo_id]:
                del self.active_connections[vehiculo_id]

    async def broadcast_to_vehicle(self, vehiculo_id: int, message: dict):
        if vehiculo_id in self.active_connections:
            for connection in self.active_connections[vehiculo_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

ws_manager = ConnectionManager()