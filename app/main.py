from fastapi import FastAPI
from app.routers import vehiculos, comandos, estado, historial, demos, ws

app = FastAPI(
    title="IoT Vehicle Control API",
    description="API REST y WebSockets para control e historial de vehículos IoT vinculada a Amazon RDS MySQL.",
    version="1.0.0"
)

# Registrar Routers
app.include_router(vehiculos.router)
app.include_router(comandos.router)
app.include_router(estado.router)
app.include_router(historial.router)
app.include_router(demos.router)
app.include_router(ws.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)