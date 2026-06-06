"""
models/promocion.py — Promociones activas del negocio.

Las promociones son ofertas visibles en la landing page
y en el panel del cliente. Pueden tener descuentos asociados
y aplican a servicios o categorías específicas.

Ejemplos:
  - "2x1 en coloración todos los martes"
  - "10% off en tu primer turno"
  - "Combo corte + barba $8.000"
  - "Turno gratis en tu cumpleaños"
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text,
    DateTime, Date, ForeignKey, Integer, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Promocion(Base):
    __tablename__ = "promociones"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)

    # ─── Contenido ────────────────────────────────────────────────────────────
    titulo      = Column(String(100), nullable=False)  # "2x1 en coloración"
    descripcion = Column(Text)                          # Detalle completo
    condiciones = Column(Text)                          # Letra chica
    imagen_url  = Column(String(500))                   # Banner para la landing

    # ─── Descuento vinculado ──────────────────────────────────────────────────
    # Si tiene descuento, el cliente puede aplicarlo al reservar
    descuento_id = Column(UUID(as_uuid=True), ForeignKey("descuentos.id"), nullable=True)

    # ─── Alcance ──────────────────────────────────────────────────────────────
    # Servicios o categorías a los que aplica (vacío = todos)
    servicios_ids   = Column(JSON, default=[])
    categorias_ids  = Column(JSON, default=[])

    # ─── Vigencia ─────────────────────────────────────────────────────────────
    fecha_inicio = Column(Date)
    fecha_fin    = Column(Date)

    # ─── Visibilidad ──────────────────────────────────────────────────────────
    activa             = Column(Boolean, default=True)
    visible_en_landing = Column(Boolean, default=True)
    destacada          = Column(Boolean, default=False)  # Aparece primero
    orden_display      = Column(Integer, default=1)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creada_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa    = relationship("Empresa",   backref="promociones")
    descuento  = relationship("Descuento", backref="promociones")
    creada_por = relationship("Usuario",   backref="promociones_creadas",
                               foreign_keys=[creada_por_id])

    def __repr__(self):
        return f"<Promocion {self.titulo} | activa:{self.activa}>"