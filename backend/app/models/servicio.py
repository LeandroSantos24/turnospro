"""
models/servicio.py — Servicios ofrecidos por el negocio.

Cada servicio tiene precio, duración, trabajadores que lo realizan
y configuración de reserva online. Es la base del sistema de turnos:
sin servicios no hay turnos.

La relación con Trabajador es muchos a muchos a través de
TrabajadorServicio — un servicio puede hacerlo más de un trabajador,
y un trabajador puede ofrecer más de un servicio.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text, Integer,
    Float, DateTime, ForeignKey, Table
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


# ─── Tabla de unión Trabajador ↔ Servicio (muchos a muchos) ──────────────────
# No necesita modelo propio — es solo una tabla de relación.
trabajador_servicio = Table(
    "trabajador_servicio",
    Base.metadata,
    Column("trabajador_id", UUID(as_uuid=True), ForeignKey("trabajadores.id"), primary_key=True),
    Column("servicio_id",   UUID(as_uuid=True), ForeignKey("servicios.id"),    primary_key=True),
)


class Servicio(Base):
    __tablename__ = "servicios"

    # ─── Identificación ───────────────────────────────────────────────────────
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id   = Column(UUID(as_uuid=True), ForeignKey("empresas.id"),   nullable=False)
    categoria_id = Column(UUID(as_uuid=True), ForeignKey("categorias.id"), nullable=True)

    # ─── Datos del servicio ───────────────────────────────────────────────────
    nombre      = Column(String(100), nullable=False)
    descripcion = Column(Text)
    imagen_url  = Column(String(500))

    # ─── Tiempo ───────────────────────────────────────────────────────────────
    duracion_minutos = Column(Integer, nullable=False, default=30)

    # Tiempo de preparación entre turnos (limpieza, preparación del puesto)
    # El sistema bloquea este tiempo después de cada turno de este servicio
    tiempo_preparacion_minutos = Column(Integer, default=0)

    # ─── Precios ──────────────────────────────────────────────────────────────
    precio          = Column(Float, nullable=False)       # Precio base en ARS
    precio_online   = Column(Float)     # Precio especial para reserva online (puede ser menor)
    precio_descuento = Column(Float)    # Precio en promoción (se muestra tachado el normal)

    # ─── Seña / pago anticipado ───────────────────────────────────────────────
    requiere_seña   = Column(Boolean, default=False)
    monto_seña      = Column(Float)     # Monto fijo de la seña
    porcentaje_seña = Column(Integer)   # O porcentaje del precio total

    # ─── Disponibilidad y visibilidad ─────────────────────────────────────────
    activo          = Column(Boolean, default=True)
    visible_online  = Column(Boolean, default=True)   # Aparece en la landing
    permite_reserva_online = Column(Boolean, default=True)

    # ─── Configuración de turnos ──────────────────────────────────────────────
    # Capacidad simultánea: cuántos clientes pueden tener este servicio
    # al mismo tiempo con el mismo trabajador (1 = individual, 2+ = grupal)
    capacidad_simultanea = Column(Integer, default=1)

    # Si el servicio es grupal (ej: clase de yoga), define el cupo máximo
    cupo_maximo = Column(Integer)

    # ─── Orden y presentación ─────────────────────────────────────────────────
    orden_display  = Column(Integer, default=1)
    destacado      = Column(Boolean, default=False)  # Se muestra primero en la landing

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa      = relationship("Empresa",    back_populates="servicios")
    categoria    = relationship("Categoria",  back_populates="servicios")
    trabajadores = relationship("Trabajador", secondary=trabajador_servicio, back_populates="servicios")
    turnos       = relationship("Turno",      back_populates="servicio")

    @property
    def precio_vigente(self) -> float:
        """Retorna el precio de descuento si existe, sino el precio base."""
        return self.precio_descuento if self.precio_descuento else self.precio

    def __repr__(self):
        return f"<Servicio {self.nombre} | ${self.precio} | {self.duracion_minutos}min>"