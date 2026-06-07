"""
schemas/turno.py — Contratos de datos para el módulo de turnos.
"""

import uuid
from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel, field_validator

from app.models.turno import EstadoTurno, OrigenTurno, CanceladoPor


class TurnoCreate(BaseModel):
    """
    Datos necesarios para reservar un turno.
    El sistema calcula hora_fin automáticamente
    usando la duración del servicio.
    """
    cliente_id:    uuid.UUID
    trabajador_id: uuid.UUID
    servicio_id:   uuid.UUID
    fecha:         date
    hora_inicio:   str             # "HH:MM"
    notas_cliente: Optional[str]  = None
    origen:        OrigenTurno    = OrigenTurno.PRESENCIAL
    descuento_id:  Optional[uuid.UUID] = None
    suscripcion_id: Optional[uuid.UUID] = None

    @field_validator("hora_inicio")
    @classmethod
    def validar_hora(cls, v: str) -> str:
        try:
            h, m = v.split(":")
            assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59
        except Exception:
            raise ValueError("La hora debe tener formato HH:MM (ej: 09:30)")
        return v

    @field_validator("fecha")
    @classmethod
    def validar_fecha_futura(cls, v: date) -> date:
        from datetime import date as d
        if v < d.today():
            raise ValueError("No se puede reservar un turno en una fecha pasada")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "cliente_id":    "9b1b80df-8e88-4866-a6c8-f4a343348011",
                "trabajador_id": "a7d80062-ee69-49e0-bd2f-89744e3a0343",
                "servicio_id":   "176c77e4-bd48-4b0f-b963-c2105c0a514c",
                "fecha":         "2026-06-09",
                "hora_inicio":   "10:00",
                "origen":        "presencial"
            }
        }


class TurnoCambioEstado(BaseModel):
    """Para confirmar, cancelar, marcar ausencia o reprogramar."""
    estado:             EstadoTurno
    motivo_cancelacion: Optional[str] = None
    cancelado_por:      Optional[CanceladoPor] = None
    notas_internas:     Optional[str] = None


class TurnoNotasUpdate(BaseModel):
    """El trabajador carga notas después de atender."""
    notas_post_servicio: str


class TurnoResponse(BaseModel):
    id:            uuid.UUID
    empresa_id:    uuid.UUID
    cliente_id:    uuid.UUID
    trabajador_id: uuid.UUID
    servicio_id:   uuid.UUID

    fecha:         date
    hora_inicio:   time
    hora_fin:      time
    duracion_minutos: int

    estado:        EstadoTurno
    origen:        OrigenTurno

    precio_base:     Optional[float]
    descuento_monto: float
    precio_final:    Optional[float]

    notas_cliente:       Optional[str]
    notas_internas:      Optional[str]
    notas_post_servicio: Optional[str]
    motivo_cancelacion:  Optional[str]

    cubierto_por_plan:       bool
    recordatorio_24h_enviado: bool
    recordatorio_2h_enviado:  bool

    # Datos relacionados embebidos para evitar N+1 queries en el frontend
    cliente_nombre:    Optional[str] = None
    trabajador_nombre: Optional[str] = None
    servicio_nombre:   Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TurnoListItem(BaseModel):
    """Vista compacta para el calendario y listas del panel."""
    id:            uuid.UUID
    fecha:         date
    hora_inicio:   time
    hora_fin:      time
    estado:        EstadoTurno
    origen:        OrigenTurno
    cliente_nombre:    Optional[str] = None
    trabajador_nombre: Optional[str] = None
    servicio_nombre:   Optional[str] = None
    precio_final:  Optional[float]

    class Config:
        from_attributes = True