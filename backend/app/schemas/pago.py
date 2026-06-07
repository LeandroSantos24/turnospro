"""
schemas/pago.py — Contratos de datos del módulo financiero.

Cubre: registro de pagos, cálculo de comisiones,
cierre de caja diario e historial de ventas.
"""

import uuid
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator

from app.models.pago import MetodoPago


class ConfigComisionesUpdate(BaseModel):
    """
    Actualiza los porcentajes de comisión por método de pago.
    El admin los configura una sola vez y aplican a todos los futuros pagos.
    """
    efectivo:      float = 0.0
    debito:        float = 0.0
    credito:       float = 0.0
    mercadopago:   float = 0.0
    transferencia: float = 0.0

    @field_validator("efectivo", "debito", "credito", "mercadopago", "transferencia")
    @classmethod
    def validar_porcentaje(cls, v: float) -> float:
        if not 0 <= v <= 100:
            raise ValueError("El porcentaje debe estar entre 0 y 100")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "efectivo":      0.0,
                "debito":        1.5,
                "credito":       9.0,
                "mercadopago":   5.99,
                "transferencia": 0.0
            }
        }


class PagoCreate(BaseModel):
    """
    Registra un pago para un turno atendido.
    El sistema calcula la comisión y el neto automáticamente.
    """
    turno_id:   uuid.UUID
    metodo:     MetodoPago
    monto:      float
    facturado:  bool = False
    notas:      Optional[str] = None

    @field_validator("monto")
    @classmethod
    def validar_monto(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("El monto debe ser mayor a cero")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "turno_id":  "5db58d97-a170-47f3-95aa-36ac37a489f6",
                "metodo":    "credito",
                "monto":     5000.0,
                "facturado": False
            }
        }


class PagoResponse(BaseModel):
    """Respuesta completa de un pago con todos los campos calculados."""
    id:              uuid.UUID
    empresa_id:      uuid.UUID
    turno_id:        Optional[uuid.UUID]
    cliente_id:      Optional[uuid.UUID]
    trabajador_id:   Optional[uuid.UUID]

    metodo:              MetodoPago
    monto_bruto:         float
    comision_porcentaje: float
    comision_monto:      float
    monto_neto:          float

    facturado:   bool
    notas:       Optional[str]

    # Datos enriquecidos
    cliente_nombre:    Optional[str] = None
    trabajador_nombre: Optional[str] = None
    servicio_nombre:   Optional[str] = None

    created_at: datetime

    class Config:
        from_attributes = True


class ResumenMetodo(BaseModel):
    """Subtotal por método de pago para el cierre de caja."""
    metodo:              MetodoPago
    cantidad_pagos:      int
    monto_bruto:         float
    comision_porcentaje: float
    comision_monto:      float
    monto_neto:          float


class CierreCaja(BaseModel):
    """
    Cierre de caja de un día.
    Resume toda la actividad financiera con el desglose por método.
    """
    fecha:             date
    empresa_id:        uuid.UUID

    # Totales del día
    total_turnos:      int
    turnos_atendidos:  int
    turnos_ausentes:   int
    turnos_cancelados: int

    # Facturación
    monto_bruto_total:  float
    comision_total:     float
    monto_neto_total:   float
    facturado_monto:    float
    no_facturado_monto: float

    # Desglose por método
    por_metodo: List[ResumenMetodo]

    # Mejor hora y trabajador del día
    hora_pico:          Optional[str] = None
    trabajador_top:     Optional[str] = None
    servicio_top:       Optional[str] = None
    ticket_promedio:    float = 0.0