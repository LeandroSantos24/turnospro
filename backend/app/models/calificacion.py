"""
models/calificacion.py — Calificaciones post-turno.

El cliente recibe un mensaje de WhatsApp después de ser atendido
y puede calificar la experiencia con puntaje y comentario.

Los datos alimentan:
  - Reputación del trabajador (calificacion_promedio)
  - Testimonios en la landing page
  - Dashboard de calidad del negocio
  - NPS (Net Promoter Score) del negocio
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text, Integer,
    DateTime, Enum, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class Calificacion(Base):
    __tablename__ = "calificaciones"

    # ─── Identificación ───────────────────────────────────────────────────────
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id    = Column(UUID(as_uuid=True), ForeignKey("empresas.id"),     nullable=False)
    turno_id      = Column(UUID(as_uuid=True), ForeignKey("turnos.id"),       nullable=False, unique=True)
    cliente_id    = Column(UUID(as_uuid=True), ForeignKey("clientes.id"),     nullable=False)
    trabajador_id = Column(UUID(as_uuid=True), ForeignKey("trabajadores.id"), nullable=False)

    # ─── Puntaje ──────────────────────────────────────────────────────────────
    puntaje          = Column(Integer, nullable=False)   # 1 a 5 estrellas
    lo_recomendaria  = Column(Boolean)                   # ¿Recomendaría el negocio? → NPS

    # ─── Comentario del cliente ───────────────────────────────────────────────
    comentario       = Column(Text)

    # Aspectos positivos y de mejora en formato estructurado
    # Ej positivos:  ["atención", "puntualidad", "resultado"]
    # Ej mejoras:    ["precio", "espera"]
    aspectos_positivos = Column(JSON, default=[])
    aspectos_mejora    = Column(JSON, default=[])

    # ─── Respuesta del negocio ────────────────────────────────────────────────
    # El admin puede responder la calificación (se muestra en la landing)
    respuesta_negocio    = Column(Text)
    respuesta_usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    respuesta_at         = Column(DateTime)

    # ─── Visibilidad ──────────────────────────────────────────────────────────
    visible_en_landing = Column(Boolean, default=False)  # El admin decide cuáles mostrar
    verificada         = Column(Boolean, default=True)   # Siempre True (vienen de clientes reales)

    # ─── Canal por donde llegó la calificación ────────────────────────────────
    canal = Column(String(20), default="whatsapp")  # whatsapp, email, presencial

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa    = relationship("Empresa",    backref="calificaciones")
    turno      = relationship("Turno",      back_populates="calificacion")
    cliente    = relationship("Cliente",    backref="calificaciones")
    trabajador = relationship("Trabajador", backref="calificaciones")

    def __repr__(self):
        return f"<Calificacion ⭐{self.puntaje} | turno:{self.turno_id}>"