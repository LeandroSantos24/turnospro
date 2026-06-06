"""
schemas/trabajador.py — Contratos de datos para trabajadores.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr

from app.models.trabajador import EstadoTrabajador


class TrabajadorCreate(BaseModel):
    nombre:    str
    apellido:  Optional[str]       = None
    email:     Optional[EmailStr]  = None
    telefono:  Optional[str]       = None
    bio_corta: Optional[str]       = None
    especialidades:   Optional[List[str]] = None
    anos_experiencia: Optional[int]       = None
    instagram_url:    Optional[str]       = None
    color_agenda:     Optional[str]       = "#2563EB"
    orden_display:    Optional[int]       = 1
    horarios:         Optional[Any]       = None

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Martín",
                "apellido": "González",
                "telefono": "2614987654",
                "especialidades": ["Corte masculino", "Barba", "Cejas"],
                "color_agenda": "#059669"
            }
        }


class TrabajadorUpdate(BaseModel):
    nombre:           Optional[str]  = None
    apellido:         Optional[str]  = None
    email:            Optional[str]  = None
    telefono:         Optional[str]  = None
    foto_url:         Optional[str]  = None
    bio_corta:        Optional[str]  = None
    bio_completa:     Optional[str]  = None
    especialidades:   Optional[List[str]] = None
    anos_experiencia: Optional[int]  = None
    instagram_url:    Optional[str]  = None
    color_agenda:     Optional[str]  = None
    orden_display:    Optional[int]  = None
    horarios:         Optional[Any]  = None
    dias_bloqueados:  Optional[List[str]] = None
    activo:           Optional[bool] = None
    estado:           Optional[EstadoTrabajador] = None


class TrabajadorResponse(BaseModel):
    id:               uuid.UUID
    empresa_id:       uuid.UUID
    nombre:           str
    apellido:         Optional[str]
    email:            Optional[str]
    telefono:         Optional[str]
    foto_url:         Optional[str]
    bio_corta:        Optional[str]
    bio_completa:     Optional[str]
    especialidades:   Optional[List[str]]
    anos_experiencia: Optional[int]
    instagram_url:    Optional[str]
    color_agenda:     str
    orden_display:    int
    horarios:         Optional[Any]
    dias_bloqueados:  Optional[List[str]]
    calificacion_promedio: float
    total_calificaciones:  int
    total_atenciones:      int
    ticket_promedio:       float
    activo:               bool
    estado:               EstadoTrabajador
    created_at:           datetime
    updated_at:           Optional[datetime]

    class Config:
        from_attributes = True