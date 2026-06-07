"""
models/pago.py — Registro de pagos vinculados a turnos.

Cada turno puede tener uno o más pagos asociados.
Soporta pagos parciales, múltiples métodos y reembolsos.

Alimenta el dashboard financiero:
  - Facturación bruta, comisiones y neto real en el bolsillo
  - Ingresos por servicio / trabajador
  - Ticket promedio
  - Métodos de pago más usados
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text, Float,
    DateTime, Enum, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class MetodoPago(str, enum.Enum):
    EFECTIVO      = "efectivo"
    TRANSFERENCIA = "transferencia"
    MERCADOPAGO   = "mercadopago"
    DEBITO        = "debito"
    CREDITO       = "credito"
    GIFT_CARD     = "gift_card"
    SUSCRIPCION   = "suscripcion"
    OTRO          = "otro"


class EstadoPago(str, enum.Enum):
    PENDIENTE   = "pendiente"
    PAGADO      = "pagado"
    PARCIAL     = "parcial"
    REEMBOLSADO = "reembolsado"
    FALLIDO     = "fallido"
    CANCELADO   = "cancelado"


class Pago(Base):
    __tablename__ = "pagos"

    # ─── Identificación ───────────────────────────────────────────────────────
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id    = Column(UUID(as_uuid=True), ForeignKey("empresas.id"),    nullable=False)
    turno_id      = Column(UUID(as_uuid=True), ForeignKey("turnos.id"),      nullable=False)
    cliente_id    = Column(UUID(as_uuid=True), ForeignKey("clientes.id"),    nullable=False)
    trabajador_id = Column(UUID(as_uuid=True), ForeignKey("trabajadores.id"), nullable=True)

    # ─── Montos brutos (lo que paga el cliente) ───────────────────────────────
    monto           = Column(Float, nullable=False)   # Precio del servicio
    monto_descuento = Column(Float, default=0.0)       # Descuento aplicado
    monto_final     = Column(Float, nullable=False)    # monto - monto_descuento

    # ─── Comisión del método de pago (costo del negocio) ─────────────────────
    # Ejemplo: tarjeta de crédito cobra 9% → el negocio pierde $450 en $5000
    monto_bruto         = Column(Float, default=0.0)   # = monto_final (alias semántico)
    comision_porcentaje = Column(Float, default=0.0)   # % vigente al momento del cobro
    comision_monto      = Column(Float, default=0.0)   # $ que se lleva el método
    monto_neto          = Column(Float, default=0.0)   # Lo que queda en el bolsillo

    # ─── Facturación ──────────────────────────────────────────────────────────
    facturado = Column(Boolean, default=False)

    # ─── Método y estado ──────────────────────────────────────────────────────
    metodo = Column(Enum(MetodoPago), nullable=False, default=MetodoPago.EFECTIVO)
    estado = Column(Enum(EstadoPago), nullable=False, default=EstadoPago.PENDIENTE)

    # ─── Referencias externas ─────────────────────────────────────────────────
    referencia_mp   = Column(String(100))
    comprobante_url = Column(String(500))

    # ─── Vínculos con descuentos y gift cards ─────────────────────────────────
    descuento_id = Column(UUID(as_uuid=True), ForeignKey("descuentos.id"),  nullable=True)
    giftcard_id  = Column(UUID(as_uuid=True), ForeignKey("gift_cards.id"),  nullable=True)

    # ─── Seña / pago anticipado ───────────────────────────────────────────────
    es_seña = Column(Boolean, default=False)

    # ─── Notas y registro ─────────────────────────────────────────────────────
    notas             = Column(Text)
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # ─── Reembolso ────────────────────────────────────────────────────────────
    reembolsado_at   = Column(DateTime)
    motivo_reembolso = Column(Text)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa        = relationship("Empresa",    backref="pagos")
    turno          = relationship("Turno",      back_populates="pagos")
    cliente        = relationship("Cliente",    backref="pagos")
    trabajador     = relationship("Trabajador", backref="pagos")
    descuento      = relationship("Descuento",  backref="pagos")
    giftcard       = relationship("GiftCard",   backref="pagos")
    registrado_por = relationship("Usuario",    backref="pagos_registrados",
                                  foreign_keys=[registrado_por_id])

    def __repr__(self):
        return f"<Pago ${self.monto_neto} neto | {self.metodo} | {self.estado}>"