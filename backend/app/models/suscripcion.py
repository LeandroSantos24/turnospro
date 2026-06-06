"""
models/suscripcion.py — Suscripción activa de un cliente a un plan.

Dos modelos en este archivo:
  - SuscripcionCliente: la suscripción activa (quién, a qué plan, desde cuándo)
  - UsoSuscripcion: cada vez que el cliente consume un crédito del plan

Flujo completo:
  1. Negocio crea PlanMembresia ("Cortes ilimitados $40k/mes")
  2. Cliente paga → se crea SuscripcionCliente (activa por 30 días)
  3. Cada turno que usa el plan → se registra UsoSuscripcion
  4. Si tipo=creditos → se descuenta 1 crédito por uso
  5. Al vencer → estado pasa a "vencida", se puede renovar
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text, Integer,
    Float, DateTime, Date, Enum, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class EstadoSuscripcion(str, enum.Enum):
    ACTIVA    = "activa"      # Vigente y usable
    PAUSADA   = "pausada"     # Pausada por el negocio (ej: vacaciones del cliente)
    VENCIDA   = "vencida"     # Expiró la fecha de fin
    CANCELADA = "cancelada"   # Cancelada antes de vencer
    PENDIENTE = "pendiente"   # Esperando confirmación de pago


class SuscripcionCliente(Base):
    __tablename__ = "suscripciones_clientes"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    plan_id    = Column(UUID(as_uuid=True), ForeignKey("planes_membresia.id"), nullable=False)

    # ─── Vigencia ─────────────────────────────────────────────────────────────
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin    = Column(Date, nullable=False)   # inicio + días del ciclo del plan

    # ─── Créditos (solo aplica si plan.tipo = CREDITOS o SESIONES) ───────────
    creditos_totales   = Column(Integer)    # Copiado del plan al suscribir
    creditos_usados    = Column(Integer, default=0)
    creditos_restantes = Column(Integer)    # None si plan es ILIMITADO

    # ─── Pago ─────────────────────────────────────────────────────────────────
    precio_pagado  = Column(Float)          # Puede diferir del plan (descuento, promo)
    descuento_id   = Column(UUID(as_uuid=True), ForeignKey("descuentos.id"), nullable=True)
    metodo_pago    = Column(String(30))     # efectivo, transferencia, mercadopago

    # ─── Estado y control ─────────────────────────────────────────────────────
    estado               = Column(Enum(EstadoSuscripcion), default=EstadoSuscripcion.PENDIENTE)
    renovacion_automatica = Column(Boolean, default=True)

    # Cuántas veces se renovó esta suscripción (para estadísticas de retención)
    numero_renovacion    = Column(Integer, default=1)

    # Referencia a la suscripción anterior si es una renovación
    renovacion_de_id     = Column(UUID(as_uuid=True), ForeignKey("suscripciones_clientes.id"), nullable=True)

    notas = Column(Text)   # Observaciones internas sobre esta suscripción

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelada_at = Column(DateTime)   # Cuándo se canceló, si aplica
    motivo_cancelacion = Column(Text)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa    = relationship("Empresa",       backref="suscripciones")
    cliente    = relationship("Cliente",       backref="suscripciones")
    plan       = relationship("PlanMembresia", back_populates="suscripciones")
    usos       = relationship("UsoSuscripcion", back_populates="suscripcion")
    renovacion_anterior = relationship("SuscripcionCliente", remote_side="SuscripcionCliente.id")

    @property
    def esta_vigente(self) -> bool:
        """Verifica si la suscripción está activa y dentro de la fecha."""
        from datetime import date
        return (
            self.estado == EstadoSuscripcion.ACTIVA and
            self.fecha_inicio <= date.today() <= self.fecha_fin
        )

    @property
    def tiene_creditos(self) -> bool:
        """True si el plan es ilimitado o si quedan créditos disponibles."""
        if self.creditos_restantes is None:
            return True   # Plan ilimitado
        return self.creditos_restantes > 0

    def __repr__(self):
        return f"<Suscripcion {self.cliente_id} | {self.plan_id} | {self.estado}>"


# ─────────────────────────────────────────────────────────────────────────────

class UsoSuscripcion(Base):
    """
    Registro de cada uso de una suscripción.

    Cada vez que un cliente usa su plan para cubrir un turno,
    se crea un registro aquí. Permite auditar todos los usos,
    saber cuándo se agotaron los créditos y calcular estadísticas
    de aprovechamiento del plan.
    """
    __tablename__ = "usos_suscripcion"

    # ─── Identificación ───────────────────────────────────────────────────────
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suscripcion_id  = Column(UUID(as_uuid=True), ForeignKey("suscripciones_clientes.id"), nullable=False)
    empresa_id      = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    turno_id        = Column(UUID(as_uuid=True), ForeignKey("turnos.id"), nullable=False)
    servicio_id     = Column(UUID(as_uuid=True), ForeignKey("servicios.id"), nullable=False)
    trabajador_id   = Column(UUID(as_uuid=True), ForeignKey("trabajadores.id"), nullable=True)

    # ─── Datos del uso ────────────────────────────────────────────────────────
    fecha_uso          = Column(DateTime, default=datetime.utcnow)

    # Créditos descontados en este uso (normalmente 1, pero puede ser más
    # si el negocio configura que un servicio premium vale 2 créditos)
    creditos_descontados = Column(Integer, default=1)

    # Usuario del sistema que validó el uso (recepcionista, trabajador)
    validado_por_id    = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    notas = Column(Text)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    suscripcion  = relationship("SuscripcionCliente", back_populates="usos")
    turno        = relationship("Turno",      backref="uso_suscripcion")
    servicio     = relationship("Servicio",   backref="usos_suscripcion")
    trabajador   = relationship("Trabajador", backref="usos_suscripcion")

    def __repr__(self):
        return f"<UsoSuscripcion {self.suscripcion_id} | turno:{self.turno_id} | -{self.creditos_descontados}cr>"