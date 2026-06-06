"""
models/plan_membresia.py — Planes de suscripción interna del negocio.

Define los planes que el negocio ofrece a sus clientes.
Ejemplos:
  - "Cortes ilimitados" → $40.000/mes, sin límite de usos
  - "Pack masajes" → $60.000/mes, 4 sesiones por ciclo
  - "Pilates mensual" → $35.000/mes, 8 clases por ciclo

Separa la DEFINICIÓN del plan (este modelo) de la
SUSCRIPCIÓN activa de cada cliente (SuscripcionCliente).
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text, Integer,
    Float, DateTime, Enum, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TipoPlan(str, enum.Enum):
    ILIMITADO = "ilimitado"   # Sin límite de usos en el ciclo
    CREDITOS  = "creditos"    # N usos por ciclo (ej: 4 masajes/mes)
    SESIONES  = "sesiones"    # N sesiones totales (no se renueva)


class CicloPlan(str, enum.Enum):
    SEMANAL   = "semanal"     # 7 días
    QUINCENAL = "quincenal"   # 15 días
    MENSUAL   = "mensual"     # 30 días
    BIMESTRAL = "bimestral"   # 60 días
    TRIMESTRAL= "trimestral"  # 90 días
    SEMESTRAL = "semestral"   # 180 días
    ANUAL     = "anual"       # 365 días


class PlanMembresia(Base):
    __tablename__ = "planes_membresia"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)

    # ─── Datos del plan ───────────────────────────────────────────────────────
    nombre      = Column(String(100), nullable=False)  # "Cortes ilimitados enero"
    descripcion = Column(Text)                          # Descripción visible al cliente
    color       = Column(String(7), default="#2563EB")  # Para la tarjeta visual

    # ─── Tipo y precio ────────────────────────────────────────────────────────
    tipo  = Column(Enum(TipoPlan),  nullable=False, default=TipoPlan.ILIMITADO)
    ciclo = Column(Enum(CicloPlan), nullable=False, default=CicloPlan.MENSUAL)
    precio = Column(Float, nullable=False)              # Precio por ciclo en ARS

    # ─── Límite de usos (solo si tipo = CREDITOS o SESIONES) ─────────────────
    # Si tipo = ILIMITADO, este campo es None
    # Si tipo = CREDITOS → se resetea cada ciclo (ej: 4 masajes/mes)
    # Si tipo = SESIONES → son sesiones totales que no se renuevan
    creditos_por_ciclo = Column(Integer)

    # ─── Servicios incluidos ──────────────────────────────────────────────────
    # JSON con lista de servicio_ids que cubre el plan.
    # Si está vacío → cubre TODOS los servicios de la empresa.
    # Ej: ["uuid-corte", "uuid-barba"] → solo esos servicios
    servicios_incluidos = Column(JSON, default=[])

    # ─── Restricciones ────────────────────────────────────────────────────────
    # Cuántos suscriptores activos puede tener este plan al mismo tiempo.
    # None = sin límite de cupos.
    max_suscriptores    = Column(Integer)

    # Días de anticipación mínima para reservar con el plan.
    anticipacion_minima_hs = Column(Integer, default=0)

    # Si el plan se renueva solo al vencer.
    renovacion_automatica = Column(Boolean, default=True)

    # ─── Visibilidad ──────────────────────────────────────────────────────────
    visible_para_clientes = Column(Boolean, default=True)  # Se muestra en la landing
    activo                = Column(Boolean, default=True)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa       = relationship("Empresa", backref="planes_membresia")
    suscripciones = relationship("SuscripcionCliente", back_populates="plan")

    def __repr__(self):
        tipo = f"{self.creditos_por_ciclo} créditos" if self.creditos_por_ciclo else "ilimitado"
        return f"<PlanMembresia {self.nombre} | ${self.precio} | {tipo}>"