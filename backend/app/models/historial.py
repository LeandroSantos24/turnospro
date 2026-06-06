"""
models/historial.py — Historial cronológico del cliente.

Registra TODOS los eventos importantes de un cliente
en el negocio en orden cronológico.

Es la "línea de tiempo" del cliente — el trabajador puede
ver de un vistazo todo lo que pasó: visitas, ausencias,
notas, puntos ganados, campañas recibidas, gift cards usadas.

Tipos de evento:
  - VISITA: completó un turno
  - AUSENCIA: no vino sin avisar
  - NOTA: el staff agregó una observación
  - PUNTOS: ganó o canjeó puntos de fidelización
  - SUSCRIPCION: se suscribió o renovó un plan
  - GIFT_CARD: usó o recibió una gift card
  - CAMPAÑA: recibió y respondió una campaña
  - CALIFICACION: dejó una calificación
  - CONTACTO: el staff lo contactó manualmente
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, DateTime,
    Enum, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TipoEvento(str, enum.Enum):
    VISITA        = "visita"
    AUSENCIA      = "ausencia"
    NOTA          = "nota"
    PUNTOS        = "puntos"
    SUSCRIPCION   = "suscripcion"
    GIFT_CARD     = "gift_card"
    CAMPANA       = "campana"
    CALIFICACION  = "calificacion"
    CONTACTO      = "contacto"
    DESCUENTO     = "descuento"
    REFERIDO      = "referido"    # Trajo un cliente nuevo


class HistorialCliente(Base):
    __tablename__ = "historial_clientes"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"),  nullable=False)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"),  nullable=False)

    # ─── Tipo de evento ───────────────────────────────────────────────────────
    tipo_evento = Column(Enum(TipoEvento), nullable=False)

    # ─── Descripción legible ──────────────────────────────────────────────────
    # Texto que se muestra en la línea de tiempo del cliente
    # Ej: "Corte de cabello con Martín · ⭐4/5"
    # Ej: "No vino al turno sin avisar"
    # Ej: "Se suscribió al plan Cortes Ilimitados"
    descripcion = Column(Text, nullable=False)

    # ─── Referencias opcionales ───────────────────────────────────────────────
    # Según el tipo de evento, puede referenciar distintas entidades
    turno_id        = Column(UUID(as_uuid=True), ForeignKey("turnos.id"),       nullable=True)
    calificacion_id = Column(UUID(as_uuid=True), ForeignKey("calificaciones.id"), nullable=True)
    suscripcion_id  = Column(UUID(as_uuid=True), ForeignKey("suscripciones_clientes.id"), nullable=True)
    giftcard_id     = Column(UUID(as_uuid=True), ForeignKey("gift_cards.id"),   nullable=True)
    descuento_id    = Column(UUID(as_uuid=True), ForeignKey("descuentos.id"),   nullable=True)

    # ─── Datos extra ──────────────────────────────────────────────────────────
    # JSON flexible para datos adicionales según el tipo de evento.
    # VISITA:      {"servicio": "Corte", "trabajador": "Martín", "precio": 5000}
    # PUNTOS:      {"puntos": 50, "motivo": "visita", "saldo_anterior": 200}
    # REFERIDO:    {"cliente_referido": "Juan López", "bonus_puntos": 100}
    # CONTACTO:    {"canal": "whatsapp", "mensaje": "Te esperamos pronto!"}
    datos_extra = Column(JSON, default={})

    # ─── Quién generó el evento ───────────────────────────────────────────────
    # None si lo generó el sistema automáticamente
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # ─── Timestamp ────────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa    = relationship("Empresa",  backref="historial_eventos")
    cliente    = relationship("Cliente",  backref="historial")
    turno      = relationship("Turno",    backref="eventos_historial",
                               foreign_keys=[turno_id])
    creado_por = relationship("Usuario",  backref="eventos_creados",
                               foreign_keys=[creado_por_id])

    def __repr__(self):
        return f"<Historial {self.tipo_evento} | cliente:{self.cliente_id} | {self.created_at}>"