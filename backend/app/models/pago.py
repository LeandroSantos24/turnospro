"""
models/pago.py — Registro de pagos vinculados a turnos.

Cada turno puede tener uno o más pagos asociados.
Soporta pagos parciales, múltiples métodos y reembolsos.

Ejemplos:
  - Turno $5.000: pago único en efectivo → 1 registro
  - Turno $10.000 + seña de $3.000: seña online + resto presencial → 2 registros
  - Turno cubierto con gift card parcial: 1 pago GC + 1 pago efectivo → 2 registros

Alimenta el dashboard financiero:
  - Facturación total del negocio
  - Ingresos por servicio / trabajador
  - Ticket promedio
  - Descuentos otorgados
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
    SUSCRIPCION   = "suscripcion"   # Cubierto por plan de membresía
    OTRO          = "otro"


class EstadoPago(str, enum.Enum):
    PENDIENTE   = "pendiente"    # Registrado pero no confirmado
    PAGADO      = "pagado"       # Confirmado y recibido
    PARCIAL     = "parcial"      # Pago parcial (queda saldo pendiente)
    REEMBOLSADO = "reembolsado"  # Devuelto al cliente
    FALLIDO     = "fallido"      # Intento de pago que no se completó
    CANCELADO   = "cancelado"    # Anulado antes de procesarse


class Pago(Base):
    __tablename__ = "pagos"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"),   nullable=False)
    turno_id   = Column(UUID(as_uuid=True), ForeignKey("turnos.id"),     nullable=False)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"),   nullable=False)

    # ─── Montos ───────────────────────────────────────────────────────────────
    monto              = Column(Float, nullable=False)
    monto_descuento    = Column(Float, default=0.0)
    monto_final        = Column(Float, nullable=False)  # monto - monto_descuento

    # ─── Método de pago ───────────────────────────────────────────────────────
    metodo = Column(Enum(MetodoPago), nullable=False, default=MetodoPago.EFECTIVO)
    estado = Column(Enum(EstadoPago), nullable=False, default=EstadoPago.PENDIENTE)

    # ─── Referencias externas ─────────────────────────────────────────────────
    # ID de la transacción en MercadoPago, si aplica
    referencia_mp      = Column(String(100))
    # URL del comprobante (factura, recibo escaneado, captura de transferencia)
    comprobante_url    = Column(String(500))

    # ─── Vínculos con descuentos y gift cards ─────────────────────────────────
    descuento_id  = Column(UUID(as_uuid=True), ForeignKey("descuentos.id"),  nullable=True)
    giftcard_id   = Column(UUID(as_uuid=True), ForeignKey("gift_cards.id"),  nullable=True)

    # ─── Es seña / pago anticipado? ───────────────────────────────────────────
    es_seña = Column(Boolean, default=False)

    # ─── Notas ────────────────────────────────────────────────────────────────
    notas = Column(Text)

    # ─── Quién registró el pago ───────────────────────────────────────────────
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # ─── Reembolso ────────────────────────────────────────────────────────────
    reembolsado_at     = Column(DateTime)
    motivo_reembolso   = Column(Text)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa        = relationship("Empresa",   backref="pagos")
    turno          = relationship("Turno",     back_populates="pagos")
    cliente        = relationship("Cliente",   backref="pagos")
    descuento      = relationship("Descuento", backref="pagos")
    giftcard       = relationship("GiftCard",  backref="pagos")
    registrado_por = relationship("Usuario",   backref="pagos_registrados",
                                  foreign_keys=[registrado_por_id])

    def __repr__(self):
        return f"<Pago ${self.monto_final} | {self.metodo} | {self.estado}>"