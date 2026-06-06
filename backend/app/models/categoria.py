"""
models/categoria.py — Categorías de servicios.

Agrupa los servicios por tipo para facilitar la navegación
en la landing page y la segmentación en estadísticas.

Ejemplos por rubro:
  Barbería   → Cortes, Barba, Cejas, Tratamientos
  Estética   → Facial, Corporal, Uñas, Depilación
  Kinesiología → Traumatológica, Deportiva, Neurológica
  Nutrición  → Consulta, Seguimiento, Plan alimentario
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)

    # ─── Datos ────────────────────────────────────────────────────────────────
    nombre        = Column(String(100), nullable=False)
    descripcion   = Column(String(255))
    icono         = Column(String(10))           # Emoji o nombre de ícono
    color         = Column(String(7), default="#2563EB")   # Hex para la UI
    orden_display = Column(Integer, default=1)   # Orden en landing page
    activo        = Column(Boolean, default=True)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa   = relationship("Empresa",  backref="categorias")
    servicios = relationship("Servicio", back_populates="categoria")

    def __repr__(self):
        return f"<Categoria {self.nombre}>"