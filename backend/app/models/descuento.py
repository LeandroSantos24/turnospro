"""
models/descuento.py — Descuentos y cupones.

Define los descuentos que el negocio puede crear para:
  - Campañas de captación ("primer turno 20% off")
  - Fidelización ("clientes VIP 15% siempre")
  - Recuperación de inactivos ("volvé con $2.000 de descuento")
  - Promociones por fecha (Día de la Madre, etc.)
  - Cupones de referido

El descuento se aplica al crear un Pago — se registra
el monto_descuento y la referencia al descuento usado.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text, Float,
    DateTime, Date, Enum, ForeignKey, Integer, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TipoDescuento(str, enum.Enum):
    PORCENTAJE  = "porcentaje"    # 20% off → precio * 0.80
    MONTO_FIJO  = "monto_fijo"    # $2.000 off → precio - 2000
    GRATIS      = "gratis"        # 100% off (primer turno gratis)


class Descuento(Base):
    __tablename__ = "descuentos"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)

    # ─── Datos del descuento ──────────────────────────────────────────────────
    codigo      = Column(String(30), nullable=False)   # El cliente lo ingresa al reservar
    nombre      = Column(String(100), nullable=False)  # Nombre interno para el admin
    descripcion = Column(Text)                         # Descripción visible al cliente

    # ─── Tipo y valor ─────────────────────────────────────────────────────────
    tipo  = Column(Enum(TipoDescuento), nullable=False)
    valor = Column(Float, nullable=False)    # % si es PORCENTAJE, ARS si es MONTO_FIJO

    # Tope máximo de descuento en ARS (para que un 50% no descuente $50.000)
    descuento_maximo_ars = Column(Float)

    # ─── Condiciones de aplicación ────────────────────────────────────────────
    # Monto mínimo del turno para poder aplicar el descuento
    monto_minimo = Column(Float, default=0.0)

    # Servicios en los que aplica (vacío = todos)
    # Ej: ["uuid-corte", "uuid-barba"]
    servicios_validos = Column(JSON, default=[])

    # Categorías en las que aplica (vacío = todas)
    categorias_validas = Column(JSON, default=[])

    # Trabajadores con los que aplica (vacío = todos)
    trabajadores_validos = Column(JSON, default=[])

    # ─── Límites de uso ───────────────────────────────────────────────────────
    usos_maximos_total    = Column(Integer)    # Total de usos permitidos (None = sin límite)
    usos_actuales         = Column(Integer, default=0)
    un_uso_por_cliente    = Column(Boolean, default=True)   # Cada cliente lo usa 1 sola vez
    solo_primera_vez      = Column(Boolean, default=False)  # Solo clientes nuevos

    # ─── Vigencia ─────────────────────────────────────────────────────────────
    fecha_inicio = Column(Date)
    fecha_fin    = Column(Date)    # None = no vence
    activo       = Column(Boolean, default=True)

    # ─── Origen del descuento ─────────────────────────────────────────────────
    # Para saber si fue creado manualmente o por una campaña automática
    campana_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campanas_fidelizacion.id", use_alter=True, name="fk_descuento_campana"),
        nullable=True
    )
    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at   = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa     = relationship("Empresa",  backref="descuentos")
    creado_por  = relationship("Usuario",  backref="descuentos_creados",
                               foreign_keys=[creado_por_id])

    @property
    def esta_vigente(self) -> bool:
        """Verifica si el descuento está activo y dentro de las fechas."""
        from datetime import date
        if not self.activo:
            return False
        hoy = date.today()
        if self.fecha_inicio and hoy < self.fecha_inicio:
            return False
        if self.fecha_fin and hoy > self.fecha_fin:
            return False
        if self.usos_maximos_total and self.usos_actuales >= self.usos_maximos_total:
            return False
        return True

    def calcular_descuento(self, precio: float) -> float:
        """Calcula el monto de descuento para un precio dado."""
        if self.tipo == TipoDescuento.GRATIS:
            return precio
        elif self.tipo == TipoDescuento.PORCENTAJE:
            descuento = precio * (self.valor / 100)
        else:   # MONTO_FIJO
            descuento = self.valor
        if self.descuento_maximo_ars:
            descuento = min(descuento, self.descuento_maximo_ars)
        return round(min(descuento, precio), 2)

    def __repr__(self):
        return f"<Descuento {self.codigo} | {self.tipo} {self.valor}>"