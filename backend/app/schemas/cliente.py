"""
schemas/cliente.py — Contratos de datos para el módulo de clientes.

Define exactamente qué datos entran y salen en cada endpoint.
Pydantic valida automáticamente — si el tipo no coincide, FastAPI
rechaza el request con 422 antes de ejecutar tu código.
"""

import uuid
from datetime import date, datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, field_validator

from app.models.cliente import (
    GeneroCliente, EstadoCliente,
    NivelFidelizacion, ComoConocio
)


# ─── Schemas de entrada (lo que recibe la API) ────────────────────────────────

class ClienteCreate(BaseModel):
    """Datos mínimos para registrar un cliente nuevo."""

    # Obligatorios
    nombre:   str
    telefono: str

    # Opcionales básicos
    apellido:         Optional[str]            = None
    email:            Optional[EmailStr]       = None
    fecha_nacimiento: Optional[date]           = None
    genero:           Optional[GeneroCliente]  = None
    dni:              Optional[str]            = None
    telefono_alt:     Optional[str]            = None
    direccion:        Optional[str]            = None

    # Datos físicos (peluquería / estética)
    tipo_cabello:          Optional[str] = None
    color_cabello_natural: Optional[str] = None
    color_cabello_actual:  Optional[str] = None
    largo_cabello:         Optional[str] = None
    tipo_piel:             Optional[str] = None
    alergias:              Optional[str] = None
    medicamentos:          Optional[str] = None

    # Vida personal (para personalización y fidelización)
    ocupacion:        Optional[str]  = None
    es_padre_madre:   Optional[bool] = None
    cantidad_hijos:   Optional[int]  = None
    hijos:            Optional[List[Any]] = None
    estado_civil:     Optional[str]  = None
    nombre_pareja:    Optional[str]  = None
    fecha_aniversario: Optional[date] = None
    intereses:        Optional[List[str]] = None
    mascota:          Optional[str]  = None

    # Preferencias
    horario_preferido:   Optional[str] = None
    dia_preferido:       Optional[str] = None
    canal_preferido:     Optional[str] = "whatsapp"
    acepta_promociones:  Optional[bool] = True
    acepta_recordatorios: Optional[bool] = True
    acepta_cumpleanos:   Optional[bool] = True

    # Origen
    como_conocio:   Optional[ComoConocio] = None

    # CRM interno (solo visible para el staff)
    observaciones_internas: Optional[str] = None
    etiquetas:              Optional[List[str]] = None

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: str) -> str:
        """El teléfono debe tener al menos 8 dígitos."""
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 8:
            raise ValueError("El teléfono debe tener al menos 8 dígitos")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Juan",
                "apellido": "Pérez",
                "telefono": "2614123456",
                "email": "juan@email.com",
                "como_conocio": "instagram"
            }
        }


class ClienteUpdate(BaseModel):
    """
    Todos los campos son opcionales — se actualiza solo lo que se envía.
    PATCH semántico: si no mandás un campo, no se toca.
    """
    nombre:           Optional[str]           = None
    apellido:         Optional[str]           = None
    email:            Optional[EmailStr]      = None
    telefono:         Optional[str]           = None
    telefono_alt:     Optional[str]           = None
    fecha_nacimiento: Optional[date]          = None
    genero:           Optional[GeneroCliente] = None
    dni:              Optional[str]           = None
    direccion:        Optional[str]           = None
    foto_url:         Optional[str]           = None

    tipo_cabello:          Optional[str] = None
    color_cabello_natural: Optional[str] = None
    color_cabello_actual:  Optional[str] = None
    largo_cabello:         Optional[str] = None
    tipo_piel:             Optional[str] = None
    alergias:              Optional[str] = None
    medicamentos:          Optional[str] = None

    ocupacion:         Optional[str]  = None
    es_padre_madre:    Optional[bool] = None
    cantidad_hijos:    Optional[int]  = None
    hijos:             Optional[List[Any]] = None
    estado_civil:      Optional[str]  = None
    nombre_pareja:     Optional[str]  = None
    fecha_aniversario: Optional[date] = None
    intereses:         Optional[List[str]] = None
    mascota:           Optional[str]  = None

    horario_preferido:   Optional[str]  = None
    dia_preferido:       Optional[str]  = None
    canal_preferido:     Optional[str]  = None
    acepta_promociones:  Optional[bool] = None
    acepta_recordatorios: Optional[bool] = None
    acepta_cumpleanos:   Optional[bool] = None

    como_conocio:           Optional[ComoConocio] = None
    observaciones_internas: Optional[str] = None
    notas_ultimo_servicio:  Optional[str] = None
    etiquetas:              Optional[List[str]] = None

    estado:            Optional[EstadoCliente]    = None
    nivel_fidelizacion: Optional[NivelFidelizacion] = None


# ─── Schemas de salida (lo que devuelve la API) ───────────────────────────────

class ClienteListItem(BaseModel):
    """
    Versión compacta para listas — solo los campos necesarios.
    Evita cargar datos pesados cuando solo necesitás mostrar
    una tabla de clientes.
    """
    id:               uuid.UUID
    nombre:           str
    apellido:         Optional[str]
    telefono:         str
    email:            Optional[str]
    estado:           EstadoCliente
    nivel_fidelizacion: NivelFidelizacion
    total_visitas:    int
    ultima_visita:    Optional[datetime]
    created_at:       datetime

    class Config:
        from_attributes = True


class ClienteResponse(BaseModel):
    """
    Perfil completo del cliente — se usa en la vista de detalle.
    Incluye todos los campos CRM.
    """
    id:                uuid.UUID
    empresa_id:        uuid.UUID

    nombre:            str
    apellido:          Optional[str]
    email:             Optional[str]
    telefono:          str
    telefono_alt:      Optional[str]
    fecha_nacimiento:  Optional[date]
    genero:            Optional[GeneroCliente]
    dni:               Optional[str]
    direccion:         Optional[str]
    foto_url:          Optional[str]

    tipo_cabello:          Optional[str]
    color_cabello_natural: Optional[str]
    color_cabello_actual:  Optional[str]
    largo_cabello:         Optional[str]
    tipo_piel:             Optional[str]
    alergias:              Optional[str]
    medicamentos:          Optional[str]

    ocupacion:         Optional[str]
    es_padre_madre:    Optional[bool]
    cantidad_hijos:    Optional[int]
    hijos:             Optional[List[Any]]
    estado_civil:      Optional[str]
    nombre_pareja:     Optional[str]
    fecha_aniversario: Optional[date]
    intereses:         Optional[List[str]]
    mascota:           Optional[str]

    horario_preferido:    Optional[str]
    dia_preferido:        Optional[str]
    canal_preferido:      Optional[str]
    acepta_promociones:   Optional[bool]
    acepta_recordatorios: Optional[bool]
    acepta_cumpleanos:    Optional[bool]

    como_conocio:           Optional[ComoConocio]
    observaciones_internas: Optional[str]
    notas_ultimo_servicio:  Optional[str]
    etiquetas:              Optional[List[str]]

    estado:             EstadoCliente
    nivel_fidelizacion: NivelFidelizacion
    puntos_fidelizacion: int
    total_visitas:      int
    total_gastado:      float
    ausencias:          int
    primera_visita:     Optional[datetime]
    ultima_visita:      Optional[datetime]

    created_at:         datetime
    updated_at:         Optional[datetime]

    class Config:
        from_attributes = True


class PaginatedClientes(BaseModel):
    """Respuesta paginada para el listado de clientes."""
    items:      List[ClienteListItem]
    total:      int
    pagina:     int
    por_pagina: int
    paginas:    int