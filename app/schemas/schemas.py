from pydantic import BaseModel, Field
from typing import Optional

class VehiculoBase(BaseModel):
    nombre: str = Field(..., example="Rover Robot 01")
    modelo: str = Field(..., example="ESP32-WROOM")
    descripcion: Optional[str] = Field(None, example="Vehículo todoterreno IoT")
    microcontrolador: str = Field(..., example="ESP32")

class VehiculoCreate(VehiculoBase): 
    pass

class ComandoBase(BaseModel):
    nombre: str
    codigo: int
    activo: bool = True

class ComandoCreate(ComandoBase):
    id_vehiculo: int

class MovimientoEjecutarRequest(BaseModel):
    comando: str = Field(..., example="AVANZAR")
    origen: Optional[str] = Field("ThunderClient", example="ThunderClient")

class DemoBase(BaseModel):
    id_vehiculo: int
    nombre: str
    descripcion: str
    activa: bool = True

class MovimientoDemoCreate(BaseModel):
    id_comando: int = Field(..., gt=0, example=1)
    orden: int = Field(..., gt=0, example=1)
    duracion_ms: int = Field(..., gt=0, example=1000)
    pausa_ms: int = Field(..., ge=0, example=500)