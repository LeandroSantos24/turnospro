"""
models/turno.py — El corazón del sistema.

Registra cada reserva que se hace en el negocio.
Conecta Cliente + Trabajador + Servicio en una fecha y hora.

Estados del turno (flujo principal):
  PENDIENTE → CONFIRMADO → EN_CURSO → ATENDIDO
                         ↘ CANCELADO
                         ↘ AUSENTE (no vino sin avisar)
                         ↘ REPROGRAMADO → (nuevo turno PENDIENTE)

El origen indica cómo llegó el turno:
  - ONLINE: el cliente reservó desde la landing page
  - WHATSAPP: llegó por el chatbot de WA
  - PRESENCIAL: lo cargó la recepción en el panel
  - TELEFONO: llamó y lo cargó la recepción
"""

import uuid
from datetime import datetime, date, time
from sqlalchemy import (
    Column, String, Boolean, Text, Integer,
    Float, DateTime, Date, Time, Enum, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class EstadoTurno(str, enum.Enum):
    PENDIENTE    = "pendiente"    # Recién creado, sin confirmar
    CONFIRMADO   = "confirmado"   # Confirmado por el negocio o auto-confirmado
    EN_CURSO     = "en_curso"     # El cliente está siendo atendido ahora
    ATENDIDO     = "atendido"     # Finalizado correctamente
    CANCELADO    = "cancelado"    # Cancelado antes de la hora
    AUSENTE      = "ausente"      # No vino sin avisar (no-show)
    REPROGRAMADO = "reprogramado" # Se movió a otro horario


class OrigenTurno(str, enum.Enum):
    ONLINE      = "online"       # Reserva desde la landing page
    WHATSAPP    = "whatsapp"     # Reserva por el chatbot de WA
    PRESENCIAL  = "presencial"   # Cargado en el panel por recepción
    TELEFONO    = "telefono"     # El cliente llamó y la recepción lo cargó
    APP         = "app"          # Futuro: app móvil


class CanceladoPor(str, enum.Enum):
    CLIENTE  = "cliente"
    NEGOCIO  = "negocio"
    SISTEMA  = "sistema"    # Cancelación automática (ej: no-show tras X horas)


class Turno(Base):
    __tablename__ = "turnos"

    # ─── Identificación ───────────────────────────────────────────────────────
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id    = Column(UUID(as_uuid=True), ForeignKey("empresas.id"),     nullable=False)
    cliente_id    = Column(UUID(as_uuid=True), ForeignKey("clientes.id"),     nullable=False)
    trabajador_id = Column(UUID(as_uuid=True), ForeignKey("trabajadores.id"), nullable=False)
    servicio_id   = Column(UUID(as_uuid=True), ForeignKey("servicios.id"),    nullable=False)

    # ─── Fecha y hora ─────────────────────────────────────────────────────────
    fecha       = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin    = Column(Time, nullable=False)   # Se calcula: hora_inicio + duracion

    # ─── Estado y origen ──────────────────────────────────────────────────────
    estado  = Column(Enum(EstadoTurno),  nullable=False, default=EstadoTurno.PENDIENTE)
    origen  = Column(Enum(OrigenTurno),  nullable=False, default=OrigenTurno.PRESENCIAL)

    # ─── Precios al momento del turno ─────────────────────────────────────────
    # Se guardan los precios al momento de la reserva por si cambian después
    precio_base      = Column(Float)     # Precio del servicio al reservar
    descuento_monto  = Column(Float, default=0.0)
    precio_final     = Column(Float)     # Lo que efectivamente paga
    descuento_id     = Column(UUID(as_uuid=True), ForeignKey("descuentos.id"), nullable=True)

    # ─── Suscripción ──────────────────────────────────────────────────────────
    # Si el turno se cubre con una suscripción activa del cliente
    suscripcion_id   = Column(UUID(as_uuid=True), ForeignKey("suscripciones_clientes.id"), nullable=True)
    cubierto_por_plan = Column(Boolean, default=False)

    # ─── Seña / pago anticipado ───────────────────────────────────────────────
    requiere_seña    = Column(Boolean, default=False)
    seña_pagada      = Column(Boolean, default=False)
    monto_seña       = Column(Float)

    # ─── Notas ────────────────────────────────────────────────────────────────
    notas_cliente   = Column(Text)    # El cliente puede dejar un mensaje al reservar
    notas_internas  = Column(Text)    # Solo visible para el staff

    # Notas que carga el trabajador DESPUÉS de atender
    # Ej: "Le hice balayage con mechas, quedó muy conforme"
    notas_post_servicio = Column(Text)

    # ─── Cancelación ──────────────────────────────────────────────────────────
    cancelado_por       = Column(Enum(CanceladoPor))
    motivo_cancelacion  = Column(String(255))
    cancelado_at        = Column(DateTime)

    # ─── Reprogramación ───────────────────────────────────────────────────────
    # Si este turno es una reprogramación, referencia al turno original
    reprogramado_de_id  = Column(UUID(as_uuid=True), ForeignKey("turnos.id"), nullable=True)
    reprogramado_a_id   = Column(UUID(as_uuid=True), ForeignKey("turnos.id"), nullable=True)

    # ─── Recordatorios enviados ───────────────────────────────────────────────
    # Flags para que Celery sepa si ya envió cada recordatorio
    recordatorio_24h_enviado = Column(Boolean, default=False)
    recordatorio_2h_enviado  = Column(Boolean, default=False)
    calificacion_solicitada  = Column(Boolean, default=False)

    # ─── Check-in ─────────────────────────────────────────────────────────────
    # Hora real en que el cliente llegó y comenzó la atención
    hora_llegada_real    = Column(DateTime)
    hora_inicio_real     = Column(DateTime)
    hora_fin_real        = Column(DateTime)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa      = relationship("Empresa",             back_populates="turnos")
    cliente      = relationship("Cliente",             back_populates="turnos")
    trabajador   = relationship("Trabajador",          back_populates="turnos")
    servicio     = relationship("Servicio",            back_populates="turnos")
    calificacion = relationship("Calificacion",        back_populates="turno", uselist=False)
    pagos        = relationship("Pago",                back_populates="turno")
    mensajes_wa  = relationship("MensajeWhatsApp",     back_populates="turno")
    suscripcion  = relationship("SuscripcionCliente",  foreign_keys=[suscripcion_id])
    reprogramado_de = relationship("Turno", foreign_keys=[reprogramado_de_id], remote_side="Turno.id")

    @property
    def duracion_minutos(self) -> int:
        """Calcula la duración real del turno en minutos."""
        inicio = datetime.combine(date.today(), self.hora_inicio)
        fin    = datetime.combine(date.today(), self.hora_fin)
        return int((fin - inicio).total_seconds() / 60)

    @property
    def esta_pago(self) -> bool:
        """Verifica si el turno tiene al menos un pago completado."""
        return any(p.estado == "pagado" for p in self.pagos)

    def __repr__(self):
        return f"<Turno {self.fecha} {self.hora_inicio} | {self.estado}>"