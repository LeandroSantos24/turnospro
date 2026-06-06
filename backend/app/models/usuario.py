"""
models/usuario.py — Modelo Usuario.

Representa a las personas que tienen acceso al sistema:
administradores, trabajadores y recepcionistas.
NO es el cliente final — ese es el modelo Cliente.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class RolUsuario(str, enum.Enum):
    """Roles disponibles dentro de una empresa."""
    ADMIN          = "admin"           # Control total del negocio
    TRABAJADOR     = "trabajador"      # Ve su agenda, carga notas
    RECEPCIONISTA  = "recepcionista"   # Gestiona turnos y clientes


class Usuario(Base):
    __tablename__ = "usuarios"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)

    # ─── Datos personales ─────────────────────────────────────────────────────
    nombre   = Column(String(100), nullable=False)
    apellido = Column(String(100))
    email    = Column(String(100), nullable=False, unique=True)
    telefono = Column(String(20))
    foto_url = Column(String(500))

    # ─── Acceso al sistema ────────────────────────────────────────────────────
    password_hash  = Column(String(255), nullable=False)
    rol            = Column(Enum(RolUsuario), nullable=False, default=RolUsuario.TRABAJADOR)
    activo         = Column(Boolean, default=True)
    email_verificado = Column(Boolean, default=False)

    # ─── Control de sesión ────────────────────────────────────────────────────
    ultimo_login   = Column(DateTime)
    token_reset    = Column(String(255))       # Token para recuperar contraseña
    token_reset_exp = Column(DateTime)         # Vencimiento del token

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa    = relationship("Empresa",    back_populates="usuarios")
    trabajador = relationship("Trabajador", back_populates="usuario", uselist=False)

    def __repr__(self):
        return f"<Usuario {self.email} | {self.rol}>"