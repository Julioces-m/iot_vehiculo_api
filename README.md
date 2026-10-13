# Control e Historial de Vehículos IoT - API

## Requisitos y Ejecución Local
1. Clonar el repositorio.
2. Crear archivo `.env` tomando como base `.env.example` y configurar credenciales de AWS RDS.
3. Crear y activar entorno virtual: `python -m venv .venv`
4. Instalar dependencias: `pip install -r requirements.txt`
5. Iniciar servidor: `uvicorn app.main:app --reload --port 8000`

## Conexión WebSocket
- **URL WebSocket:** `ws://localhost:8000/ws/vehiculos/{vehiculo_id}`
- **Eventos Notificados:**
  - `conexion_inicial`: Enviado al conectarse con el estado actual del vehículo.
  - `movimiento_individual`: Emitido tras un POST exitoso de un comando individual.
  - `demo_inicio`: Emitido al arrancar una secuencia DEMO.
  - `demo_movimiento`: Emitido por cada paso de la DEMO (incluye `duracion_ms` y `pausa_ms`).
  - `demo_fin`: Emitido al concluir todos los pasos de la DEMO.
  - `demo_cancelada`: Emitido si se envía una solicitud de cancelación.