"""
models/trabajador.py — Modelo Trabajador.

Representa al profesional que atiende los turnos dentro del negocio.
Tiene agenda propia, especialidades, métricas de desempeño
y datos para su tarjeta en la landing page pública.

Un Trabajador está vinculado a un Usuario (su cuenta de acceso),
pero son entidades separadas: el Usuario maneja el login,
el Trabajador maneja la agenda y el perfil profesional.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text, Integer,
    DateTime, Float, Enum, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class EstadoTrabajador(str, enum.Enum):
    ACTIVO    = "activo"
    INACTIVO  = "inactivo"    # Baja temporal (vacaciones, licencia)
    ELIMINADO = "eliminado"   # Baja definitiva — se mantiene por historial


class Trabajador(Base):
    __tablename__ = "trabajadores"

    # ─── Identificación ───────────────────────────────────────────────────────
    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id  = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    usuario_id  = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    # nullable=True porque puede existir un trabajador sin cuenta de acceso

    # ─── Datos personales ─────────────────────────────────────────────────────
    nombre           = Column(String(100), nullable=False)
    apellido         = Column(String(100))
    email            = Column(String(100))
    telefono         = Column(String(20))
    fecha_nacimiento = Column(DateTime)
    foto_url         = Column(String(500))

    # ─── Perfil profesional (visible en landing page) ─────────────────────────
    bio_corta        = Column(String(300))
    bio_completa     = Column(Text)
    especialidades   = Column(JSON, default=[])
    # Ej: ["Corte masculino", "Barba", "Coloración", "Keratina"]
    anos_experiencia = Column(Integer)
    instagram_url    = Column(String(255))

    # ─── Agenda y disponibilidad ──────────────────────────────────────────────
    # Estructura JSON por día de semana:
    # {
    #   "lunes":    {"activo": true, "inicio": "09:00", "fin": "18:00"},
    #   "martes":   {"activo": true, "inicio": "09:00", "fin": "18:00"},
    #   "miercoles":{"activo": true, "inicio": "09:00", "fin": "13:00"},
    #   "jueves":   {"activo": true, "inicio": "09:00", "fin": "18:00"},
    #   "viernes":  {"activo": true, "inicio": "09:00", "fin": "17:00"},
    #   "sabado":   {"activo": true, "inicio": "09:00", "fin": "13:00"},
    #   "domingo":  {"activo": false}
    # }
    horarios = Column(JSON, default={})

    # Días bloqueados específicos (feriados, vacaciones, etc.)
    # Ej: ["2024-12-25", "2025-01-01"]
    dias_bloqueados = Column(JSON, default=[])

    # Duración de turno propia — sobreescribe el default de la empresa
    duracion_turno_minutos = Column(Integer)

    # Color en la vista de agenda del panel admin
    color_agenda   = Column(String(7), default="#2563EB")

    # Orden de aparición en la landing page (1 = primero)
    orden_display  = Column(Integer, default=1)

    # ─── Métricas de desempeño (se actualizan automáticamente) ───────────────
    calificacion_promedio = Column(Float, default=0.0)    # 0.0 a 5.0
    total_calificaciones  = Column(Integer, default=0)
    total_atenciones      = Column(Integer, default=0)    # Turnos completados
    total_ausencias       = Column(Integer, default=0)    # Clientes que no vinieron
    ticket_promedio       = Column(Float, default=0.0)    # Monto promedio por turno

    # ─── Estado ───────────────────────────────────────────────────────────────
    estado  = Column(Enum(EstadoTrabajador), default=EstadoTrabajador.ACTIVO)
    activo  = Column(Boolean, default=True)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa   = relationship("Empresa",   back_populates="trabajadores")
    usuario   = relationship("Usuario",   back_populates="trabajador")
    turnos    = relationship("Turno",     back_populates="trabajador")
    servicios = relationship(
        "Servicio",
        secondary="trabajador_servicio",
        back_populates="trabajadores"
    )

    def __repr__(self):
        return f"<Trabajador {self.nombre} {self.apellido} | ⭐ {self.calificacion_promedio}>"