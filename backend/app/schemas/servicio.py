"""
schemas/servicio.py — Contratos de datos para categorías y servicios.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CategoriaCreate(BaseModel):
    nombre:       str
    descripcion:  Optional[str] = None
    icono:        Optional[str] = None
    color:        Optional[str] = "#2563EB"
    orden_display: Optional[int] = 1

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Cortes",
                "icono": "✂️",
                "color": "#2563EB"
            }
        }


class CategoriaResponse(BaseModel):
    id:           uuid.UUID
    empresa_id:   uuid.UUID
    nombre:       str
    descripcion:  Optional[str]
    icono:        Optional[str]
    color:        str
    orden_display: int
    activo:       bool
    created_at:   datetime

    class Config:
        from_attributes = True


class ServicioCreate(BaseModel):
    nombre:       str
    descripcion:  Optional[str]       = None
    categoria_id: Optional[uuid.UUID] = None
    duracion_minutos: int             = 30
    precio:       float
    precio_descuento: Optional[float] = None
    imagen_url:   Optional[str]       = None
    requiere_seña: Optional[bool]     = False
    monto_seña:   Optional[float]     = None
    visible_online: Optional[bool]    = True
    permite_reserva_online: Optional[bool] = True
    destacado:    Optional[bool]      = False
    orden_display: Optional[int]      = 1

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Corte de cabello",
                "duracion_minutos": 30,
                "precio": 5000,
                "categoria_id": None
            }
        }


class ServicioUpdate(BaseModel):
    nombre:           Optional[str]        = None
    descripcion:      Optional[str]        = None
    categoria_id:     Optional[uuid.UUID]  = None
    duracion_minutos: Optional[int]        = None
    precio:           Optional[float]      = None
    precio_descuento: Optional[float]      = None
    imagen_url:       Optional[str]        = None
    requiere_seña:    Optional[bool]       = None
    monto_seña:       Optional[float]      = None
    visible_online:   Optional[bool]       = None
    permite_reserva_online: Optional[bool] = None
    activo:           Optional[bool]       = None
    destacado:        Optional[bool]       = None
    orden_display:    Optional[int]        = None
    trabajador_ids:   Optional[List[uuid.UUID]] = None


class ServicioResponse(BaseModel):
    id:               uuid.UUID
    empresa_id:       uuid.UUID
    categoria_id:     Optional[uuid.UUID]
    nombre:           str
    descripcion:      Optional[str]
    duracion_minutos: int
    precio:           float
    precio_descuento: Optional[float]
    precio_vigente:   float
    imagen_url:       Optional[str]
    requiere_seña:    bool
    monto_seña:       Optional[float]
    activo:           bool
    visible_online:   bool
    permite_reserva_online: bool
    destacado:        bool
    orden_display:    int
    created_at:       datetime

    class Config:
        from_attributes = True