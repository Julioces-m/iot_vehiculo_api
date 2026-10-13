from typing import List, Dict, Any, Optional

class StoredProcedureRepository:
    def __init__(self, connection):
        self.conn = connection

    # --- VEHÍCULOS ---
    def sp_crear_vehiculo(self, nombre: str, modelo: str, descripcion: str, microcontrolador: str) -> int:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_crear_vehiculo', (nombre, modelo, descripcion, microcontrolador))
            result = cursor.fetchone()
            return result['id_vehiculo'] if result and 'id_vehiculo' in result else cursor.lastrowid

    def sp_obtener_vehiculos(self) -> List[Dict[str, Any]]:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_obtener_vehiculos')
            return cursor.fetchall()

    def sp_obtener_vehiculo(self, id_vehiculo: int) -> Optional[Dict[str, Any]]:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_obtener_vehiculo', (id_vehiculo,))
            return cursor.fetchone()

    def sp_actualizar_vehiculo(self, id_vehiculo: int, nombre: str, modelo: str, descripcion: str, microcontrolador: str, activo: bool) -> bool:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_actualizar_vehiculo', (id_vehiculo, nombre, modelo, descripcion, microcontrolador, activo))
            return cursor.rowcount > 0

    def sp_eliminar_vehiculo(self, id_vehiculo: int) -> bool:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_eliminar_vehiculo', (id_vehiculo,))
            return cursor.rowcount > 0

    # --- COMANDOS ---
    def sp_crear_comando(self, id_vehiculo: int, nombre: str, codigo: int, descripcion: str) -> int:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_crear_comando', (id_vehiculo, nombre, codigo, descripcion))
            res = cursor.fetchone()
            return res['id_comando'] if res and 'id_comando' in res else cursor.lastrowid

    def sp_obtener_comandos_vehiculo(self, id_vehiculo: int) -> List[Dict[str, Any]]:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_obtener_comandos_vehiculo', (id_vehiculo,))
            return cursor.fetchall()

    def sp_actualizar_comando(self, id_comando: int, nombre: str, codigo: int, descripcion: str, activo: bool) -> bool:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_actualizar_comando', (id_comando, nombre, codigo, descripcion, activo))
            return cursor.rowcount > 0

    def sp_eliminar_comando(self, id_comando: int) -> bool:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_eliminar_comando', (id_comando,))
            return cursor.rowcount > 0

    # --- ESTADO ---
    def sp_actualizar_estado(self, id_vehiculo: int, id_comando: int, conectado: bool) -> bool:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_actualizar_estado', (id_vehiculo, id_comando, conectado))
            return True

    def sp_obtener_estado(self, id_vehiculo: int) -> Optional[Dict[str, Any]]:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_obtener_estado', (id_vehiculo,))
            return cursor.fetchone()

    # --- HISTORIAL ---
    def sp_registrar_historial(self, id_vehiculo: int, id_comando: int, origen: str) -> bool:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_registrar_historial', (id_vehiculo, id_comando, origen))
            return True

    def sp_obtener_historial(self, id_vehiculo: int) -> List[Dict[str, Any]]:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_obtener_historial', (id_vehiculo,))
            return cursor.fetchall()

    # --- DEMO ---
    def sp_crear_demo(self, id_vehiculo: int, nombre: str, descripcion: str) -> int:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_crear_demo', (id_vehiculo, nombre, descripcion))
            res = cursor.fetchone()
            return res['id_demo'] if res and 'id_demo' in res else cursor.lastrowid

    def sp_obtener_demos(self, id_vehiculo: int) -> List[Dict[str, Any]]:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_obtener_demos', (id_vehiculo,))
            return cursor.fetchall()

    def sp_actualizar_demo(self, id_demo: int, nombre: str, descripcion: str, activo: bool) -> bool:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_actualizar_demo', (id_demo, nombre, descripcion, activo))
            return cursor.rowcount > 0

    def sp_eliminar_demo(self, id_demo: int) -> bool:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_eliminar_demo', (id_demo,))
            return cursor.rowcount > 0

    # --- MOVIMIENTOS DEMO ---
    def sp_agregar_movimiento_demo(self, id_demo: int, id_comando: int, orden: int, duracion_ms: int, pausa_ms: int) -> bool:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_agregar_movimiento_demo', (id_demo, id_comando, orden, duracion_ms, pausa_ms))
            return True

    def sp_obtener_movimientos_demo(self, id_demo: int) -> List[Dict[str, Any]]:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_obtener_movimientos_demo', (id_demo,))
            return cursor.fetchall()

    def sp_actualizar_movimiento_demo(self, id_demo_movimiento: int, id_comando: int, orden: int, duracion_ms: int, pausa_ms: int) -> bool:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_actualizar_movimiento_demo', (id_demo_movimiento, id_comando, orden, duracion_ms, pausa_ms))
            return cursor.rowcount > 0

    def sp_eliminar_movimiento_demo(self, id_demo_movimiento: int) -> bool:
        with self.conn.cursor() as cursor:
            cursor.callproc('sp_eliminar_movimiento_demo', (id_demo_movimiento,))
            return cursor.rowcount > 0