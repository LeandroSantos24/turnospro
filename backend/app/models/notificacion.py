"""
models/notificacion.py — Notificaciones programadas.

Define QUÉ se debe enviar y CUÁNDO.
Celery revisa esta tabla cada minuto y ejecuta
las notificaciones pendientes en el momento correcto.

Separa la lógica de programación (este modelo) del
registro de envío real (MensajeWhatsApp).

Ejemplos de uso:
  - Turno creado a las 10:00 → se programa recordatorio para mañana a las 10:00
  - Cliente cumple años el 15 → se programa mensaje para el 15 a las 09:00
  - Cliente inactivo hace 30 días → se programa campaña de recuperación
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text, Integer,
    DateTime, Enum, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TipoNotificacion(str, enum.Enum):
    RECORDATORIO_24H = "recordatorio_24h"
    RECORDATORIO_2H  = "recordatorio_2h"
    CONFIRMACION     = "confirmacion"
    CALIFICACION     = "calificacion"
    CUMPLEANOS       = "cumpleanos"
    INACTIVO         = "inactivo"
    SUSCRIPCION_POR_VENCER = "suscripcion_por_vencer"
    GIFTCARD_POR_VENCER    = "giftcard_por_vencer"
    CAMPANA          = "campana"
    MANUAL           = "manual"


class CanalNotificacion(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL    = "email"
    AMBOS    = "ambos"


class EstadoNotificacion(str, enum.Enum):
    PENDIENTE  = "pendiente"   # Esperando ser procesada
    PROCESANDO = "procesando"  # Celery la está ejecutando ahora
    ENVIADA    = "enviada"     # Se ejecutó y se creó el MensajeWhatsApp
    FALLIDA    = "fallida"     # Error al procesar
    CANCELADA  = "cancelada"   # Se canceló (ej: el turno fue cancelado)


class Notificacion(Base):
    __tablename__ = "notificaciones"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"),  nullable=False)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"),  nullable=False)
    turno_id   = Column(UUID(as_uuid=True), ForeignKey("turnos.id"),    nullable=True)

    # ─── Tipo y canal ─────────────────────────────────────────────────────────
    tipo  = Column(Enum(TipoNotificacion),  nullable=False)
    canal = Column(Enum(CanalNotificacion), nullable=False, default=CanalNotificacion.WHATSAPP)

    # ─── Programación ─────────────────────────────────────────────────────────
    # Momento exacto en que Celery debe procesar esta notificación
    programada_para = Column(DateTime, nullable=False)

    # ─── Estado ───────────────────────────────────────────────────────────────
    estado   = Column(Enum(EstadoNotificacion), default=EstadoNotificacion.PENDIENTE)
    intentos = Column(Integer, default=0)

    # ─── Contenido personalizado ──────────────────────────────────────────────
    # Si está vacío, se usa la plantilla por defecto del tipo
    mensaje_personalizado = Column(Text)

    # ─── Referencia al mensaje enviado ────────────────────────────────────────
    mensaje_wa_id = Column(UUID(as_uuid=True), ForeignKey("mensajes_whatsapp.id"), nullable=True)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    procesada_at = Column(DateTime)
    error_detalle = Column(Text)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa    = relationship("Empresa",        backref="notificaciones")
    cliente    = relationship("Cliente",        backref="notificaciones")
    turno      = relationship("Turno",          backref="notificaciones",
                               foreign_keys=[turno_id])
    mensaje_wa = relationship("MensajeWhatsApp", backref="notificacion",
                               foreign_keys=[mensaje_wa_id])

    def __repr__(self):
        return f"<Notificacion {self.tipo} | {self.estado} | {self.programada_para}>"