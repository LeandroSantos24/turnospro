"""
models/giftcard.py — Gift cards con código único y QR.

El negocio puede crear gift cards para vender como regalo.
El comprador las paga, el beneficiario las usa en sus turnos.

Flujo completo:
  1. Negocio crea la gift card (monto, beneficiario, vencimiento)
  2. Sistema genera código único + QR
  3. Se envía por WhatsApp al beneficiario (o se imprime en el local)
  4. El beneficiario reserva un turno y aplica el código
  5. Se descuenta del saldo restante
  6. Si no alcanza, paga la diferencia con otro método

Soporta uso parcial: una gift card de $10.000 puede usarse
en múltiples turnos hasta agotar el saldo.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text, Float,
    DateTime, Date, Enum, ForeignKey, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class EstadoGiftCard(str, enum.Enum):
    ACTIVA    = "activa"      # Disponible para usar
    USADA     = "usada"       # Saldo agotado completamente
    VENCIDA   = "vencida"     # Pasó la fecha de vencimiento
    ANULADA   = "anulada"     # Anulada por el negocio


class GiftCard(Base):
    __tablename__ = "gift_cards"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)

    # Código único alfanumérico que se muestra en el QR y en el físico
    # Ej: "TURNO-XK7P-2024"
    codigo     = Column(String(30), nullable=False, unique=True)

    # URL de la imagen del QR generada (se guarda en storage)
    qr_url     = Column(String(500))

    # ─── Saldo ────────────────────────────────────────────────────────────────
    monto_original  = Column(Float, nullable=False)
    saldo_restante  = Column(Float, nullable=False)    # Se descuenta con cada uso

    # ─── Datos del comprador ──────────────────────────────────────────────────
    # Quien pagó la gift card (puede o no ser cliente del sistema)
    comprador_nombre   = Column(String(100))
    comprador_telefono = Column(String(20))
    comprador_email    = Column(String(100))
    # Si el comprador es un cliente registrado
    comprador_cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=True)

    # ─── Datos del beneficiario ───────────────────────────────────────────────
    # A quién va dirigida la gift card
    beneficiario_nombre   = Column(String(100))
    beneficiario_telefono = Column(String(20))
    beneficiario_email    = Column(String(100))
    # Si el beneficiario es un cliente registrado
    beneficiario_cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=True)

    # ─── Mensaje personalizado ────────────────────────────────────────────────
    # Texto que acompaña la gift card (ej: "¡Feliz cumpleaños! Con cariño, Mamá")
    mensaje_personalizado = Column(Text)

    # ─── Vencimiento ──────────────────────────────────────────────────────────
    fecha_vencimiento = Column(Date)    # None = no vence

    # ─── Estado ───────────────────────────────────────────────────────────────
    estado = Column(Enum(EstadoGiftCard), default=EstadoGiftCard.ACTIVA)

    # ─── Servicios restringidos ───────────────────────────────────────────────
    # Si está vacío, sirve para cualquier servicio del negocio
    # Si tiene valores, solo para esos servicios
    # Ej: ["uuid-corte", "uuid-barba"]
    servicios_validos = Column(String(500))   # JSON como string

    # ─── Envío y entrega ──────────────────────────────────────────────────────
    enviada_por_whatsapp = Column(Boolean, default=False)
    fecha_envio_whatsapp = Column(DateTime)
    enviada_por_email    = Column(Boolean, default=False)
    fecha_envio_email    = Column(DateTime)
    impresa              = Column(Boolean, default=False)   # Se imprimió en el local

    # ─── Quién la creó ────────────────────────────────────────────────────────
    creada_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usada_at   = Column(DateTime)    # Cuándo se agotó el saldo

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa              = relationship("Empresa",  backref="gift_cards")
    comprador_cliente    = relationship("Cliente",  foreign_keys=[comprador_cliente_id],
                                        backref="gift_cards_compradas")
    beneficiario_cliente = relationship("Cliente",  foreign_keys=[beneficiario_cliente_id],
                                        backref="gift_cards_recibidas")
    creada_por           = relationship("Usuario",  backref="gift_cards_creadas",
                                        foreign_keys=[creada_por_id])

    @property
    def esta_vigente(self) -> bool:
        """Verifica si la gift card tiene saldo y no venció."""
        from datetime import date
        if self.estado != EstadoGiftCard.ACTIVA:
            return False
        if self.fecha_vencimiento and date.today() > self.fecha_vencimiento:
            return False
        return self.saldo_restante > 0

    @property
    def porcentaje_usado(self) -> float:
        """Porcentaje del saldo que ya fue consumido."""
        if self.monto_original == 0:
            return 0
        return round((1 - self.saldo_restante / self.monto_original) * 100, 1)

    def __repr__(self):
        return f"<GiftCard {self.codigo} | ${self.saldo_restante} restante | {self.estado}>"