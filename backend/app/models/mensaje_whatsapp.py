"""
models/mensaje_whatsapp.py — Log de mensajes de WhatsApp.

Registra TODOS los mensajes enviados y recibidos por WhatsApp
en la plataforma. Sirve para:

  - Auditoría completa de comunicaciones
  - Saber si el cliente recibió y leyó el recordatorio
  - Analizar tasa de respuesta por tipo de mensaje
  - Base para el chatbot (historial de conversación)
  - Detectar mensajes que fallaron y reintentar

Estados del mensaje (ciclo de vida en WhatsApp):
  PENDIENTE → ENVIADO → ENTREGADO → LEIDO
           ↘ FALLIDO (error de envío)
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text,
    DateTime, Enum, ForeignKey, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TipoMensaje(str, enum.Enum):
    CONFIRMACION   = "confirmacion"    # Confirma el turno al reservar
    RECORDATORIO   = "recordatorio"    # 24h o 2h antes del turno
    CANCELACION    = "cancelacion"     # Avisa que el turno fue cancelado
    REPROGRAMACION = "reprogramacion"  # Avisa el nuevo horario
    CALIFICACION   = "calificacion"    # Pide calificación post-turno
    BIENVENIDA     = "bienvenida"      # Primer mensaje al nuevo cliente
    CUMPLEANOS     = "cumpleanos"      # Saludo de cumpleaños con promo
    INACTIVO       = "inactivo"        # Recuperación de cliente inactivo
    PROMOCION      = "promocion"       # Campaña de marketing
    CHATBOT        = "chatbot"         # Conversación del chatbot
    MANUAL         = "manual"          # Enviado manualmente por el staff


class DireccionMensaje(str, enum.Enum):
    ENVIADO   = "enviado"    # TurnosPro → Cliente
    RECIBIDO  = "recibido"   # Cliente → TurnosPro


class EstadoMensaje(str, enum.Enum):
    PENDIENTE  = "pendiente"    # En cola, aún no enviado
    ENVIADO    = "enviado"      # Enviado a la API de WhatsApp
    ENTREGADO  = "entregado"    # Llegó al teléfono del cliente
    LEIDO      = "leido"        # El cliente abrió el mensaje
    FALLIDO    = "fallido"      # Error al enviar
    CANCELADO  = "cancelado"    # Se canceló antes de enviar


class MensajeWhatsApp(Base):
    __tablename__ = "mensajes_whatsapp"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"),  nullable=False)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"),  nullable=False)
    turno_id   = Column(UUID(as_uuid=True), ForeignKey("turnos.id"),    nullable=True)

    # ─── Datos del mensaje ────────────────────────────────────────────────────
    tipo       = Column(Enum(TipoMensaje),      nullable=False)
    direccion  = Column(Enum(DireccionMensaje), nullable=False, default=DireccionMensaje.ENVIADO)
    estado     = Column(Enum(EstadoMensaje),    nullable=False, default=EstadoMensaje.PENDIENTE)

    # Número de teléfono al que se envió (formato internacional: +5492614xxxxxx)
    telefono_destino = Column(String(20), nullable=False)

    # Contenido del mensaje (texto procesado con las variables ya reemplazadas)
    contenido = Column(Text, nullable=False)

    # ─── Metadatos de WhatsApp ────────────────────────────────────────────────
    # ID del mensaje en la API de Meta (para rastrear estado y recibir webhooks)
    wa_message_id  = Column(String(100))

    # Nombre de la plantilla usada (ej: "recordatorio_turno_24h")
    plantilla_usada = Column(String(100))

    # ─── Control de reintentos ────────────────────────────────────────────────
    intentos          = Column(Integer, default=0)
    max_intentos      = Column(Integer, default=3)
    proximo_reintento = Column(DateTime)
    error_detalle     = Column(Text)    # Mensaje de error si falló

    # ─── Timestamps de estado ─────────────────────────────────────────────────
    enviado_at    = Column(DateTime)
    entregado_at  = Column(DateTime)
    leido_at      = Column(DateTime)
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa = relationship("Empresa", backref="mensajes_whatsapp")
    cliente = relationship("Cliente", backref="mensajes_whatsapp")
    turno   = relationship("Turno",   back_populates="mensajes_wa",
                            foreign_keys=[turno_id])

    def __repr__(self):
        return f"<MensajeWA {self.tipo} | {self.estado} | {self.telefono_destino}>"