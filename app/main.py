from fastapi import FastAPI
from app.routers import vehiculos, comandos, estado, historial, demos, ws
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import vehiculos, comandos, estado, historial, demos, ws

app = FastAPI(
    title="API IoT - Control de Vehículo",
    description="API RESTful y WebSockets para gestión y telemetría de vehículos IoT",
    version="1.1.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehiculos.router)
app.include_router(comandos.router)
app.include_router(estado.router)
app.include_router(historial.router)
app.include_router(demos.router)
app.include_router(ws.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)