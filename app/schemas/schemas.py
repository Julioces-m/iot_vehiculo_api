from enum import IntEnum
from typing import Optional
from pydantic import BaseModel, Field


class ComandoMovimiento(IntEnum):
    AVANZAR = 1
    RETROCEDER = 2
    GIRAR_IZQUIERDA = 3
    GIRAR_DERECHA = 4
    SUBIR_BRAZO = 5
    BAJAR_BRAZO = 6
    ABRIR_PALA = 7
    CERRAR_PALA = 8
    DETENER = 9


class VehiculoBase(BaseModel):
    nombre: str = Field(..., json_schema_extra={"example": "Excavadora IoT"})
    modelo: str = Field(..., json_schema_extra={"example": "Modelo X"})
    descripcion: Optional[str] = Field(
        None,
        json_schema_extra={
            "example": "Vehículo de construcción controlado por ESP8266"
        },
    )
    microcontrolador: str = Field(
        ..., json_schema_extra={"example": "ESP8266"}
    )


class VehiculoCreate(VehiculoBase):
    pass


class ComandoBase(BaseModel):
    nombre: str
    codigo: int
    activo: bool = True


class ComandoCreate(ComandoBase):
    id_vehiculo: int


class MovimientoEjecutarRequest(BaseModel):
    comando: ComandoMovimiento = Field(
        ...,
        description="Código numérico del comando (1: AVANZAR, 2: RETROCEDER, 3: GIRAR_IZQUIERDA, 4: GIRAR_DERECHA, 5: SUBIR_BRAZO, 6: BAJAR_BRAZO, 7: ABRIR_PALA, 8: CERRAR_PALA, 9: DETENER)",
        json_schema_extra={"example": 1},
    )
    origen: Optional[str] = Field(
        "ThunderClient", json_schema_extra={"example": "ThunderClient"}
    )


class DemoBase(BaseModel):
    id_vehiculo: int
    nombre: str
    descripcion: str
    activa: bool = True


class MovimientoDemoCreate(BaseModel):
    id_comando: int = Field(..., gt=0, json_schema_extra={"example": 1})
    orden: int = Field(..., gt=0, json_schema_extra={"example": 1})
    duracion_ms: int = Field(..., gt=0, json_schema_extra={"example": 1000})
    pausa_ms: int = Field(..., ge=0, json_schema_extra={"example": 500})