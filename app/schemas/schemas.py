from pydantic import BaseModel, Field
from typing import Optional

class VehiculoBase(BaseModel):
    nombre: str
    modelo: str
    activo: bool = True

class VehiculoCreate(VehiculoBase): pass

class ComandoBase(BaseModel):
    nombre: str
    codigo: str
    activo: bool = True

class ComandoCreate(ComandoBase):
    id_vehiculo: int

class MovimientoEjecutarRequest(BaseModel):
    comando: str
    origen: Optional[str] = "ThunderClient"

class DemoBase(BaseModel):
    id_vehiculo: int
    nombre: str
    descripcion: str
    activa: bool = True

class MovimientoDemoCreate(BaseModel):
    orden: int
    comando: str
    duracion_ms: int = Field(gt=0)
    pausa_ms: int = Field(ge=0)