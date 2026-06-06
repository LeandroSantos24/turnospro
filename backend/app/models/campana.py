"""
models/campana.py — Campañas de fidelización y marketing.

Permite segmentar clientes y enviarles mensajes personalizados
con o sin descuento. El sistema calcula automáticamente
quiénes cumplen las condiciones del segmento.

Ejemplos de campañas:
  - "Clientes sin visita hace 30+ días" → mensaje de recuperación + 20% off
  - "Clientes VIP del mes" → agradecimiento + gift card $5.000
  - "Cumpleañeros de agosto" → saludo + turno gratis
  - "Clientes con 10+ visitas" → invitación a plan de suscripción

El campo segmento_reglas define los criterios en JSON:
  {
    "dias_sin_visita_min": 30,
    "dias_sin_visita_max": 90,
    "nivel_fidelizacion": ["regular", "frecuente"],
    "total_visitas_min": 5,
    "gasto_total_min": 20000,
    "tiene_suscripcion": false,
    "mes_nacimiento": 8
  }
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


class EstadoCampana(str, enum.Enum):
    BORRADOR   = "borrador"    # En preparación, aún no enviada
    PROGRAMADA = "programada"  # Lista para enviar en fecha/hora específica
    ACTIVA     = "activa"      # Enviándose ahora
    PAUSADA    = "pausada"     # Pausada manualmente
    FINALIZADA = "finalizada"  # Completada
    CANCELADA  = "cancelada"   # Cancelada antes de terminar


class CanalCampana(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL    = "email"
    AMBOS    = "ambos"


class CampanaFidelizacion(Base):
    __tablename__ = "campanas_fidelizacion"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)

    # ─── Datos de la campaña ──────────────────────────────────────────────────
    nombre      = Column(String(100), nullable=False)  # Nombre interno
    descripcion = Column(Text)                          # Para qué es esta campaña
    objetivo    = Column(String(255))                   # "Recuperar inactivos de julio"

    # ─── Segmentación ─────────────────────────────────────────────────────────
    # Reglas JSON que definen a quiénes se les envía.
    # El sistema filtra los clientes que cumplen TODAS las condiciones.
    segmento_reglas = Column(JSON, default={})

    # Cantidad de clientes que cumplen las reglas (se calcula al previsualizar)
    total_destinatarios = Column(Integer, default=0)

    # ─── Mensaje ──────────────────────────────────────────────────────────────
    canal            = Column(Enum(CanalCampana), nullable=False, default=CanalCampana.WHATSAPP)

    # Template del mensaje con variables reemplazables:
    # {{nombre_cliente}}, {{nombre_negocio}}, {{codigo_descuento}}, {{link_reserva}}
    mensaje_template = Column(Text, nullable=False)

    # Asunto (solo para email)
    asunto_email     = Column(String(200))

    # ─── Descuento asociado ───────────────────────────────────────────────────
    descuento_id = Column(UUID(as_uuid=True), ForeignKey("descuentos.id"), nullable=True)

    # ─── Programación ─────────────────────────────────────────────────────────
    fecha_ejecucion  = Column(DateTime)        # Cuándo se ejecuta (None = inmediato)
    estado           = Column(Enum(EstadoCampana), default=EstadoCampana.BORRADOR)

    # ─── Métricas de resultado ────────────────────────────────────────────────
    # Se actualizan en tiempo real mientras se ejecuta la campaña
    total_enviados    = Column(Integer, default=0)
    total_entregados  = Column(Integer, default=0)
    total_leidos      = Column(Integer, default=0)
    total_respondidos = Column(Integer, default=0)
    # Clientes que reservaron un turno después de recibir la campaña
    total_convertidos = Column(Integer, default=0)
    # Facturación generada por los clientes convertidos
    facturacion_generada = Column(Float, default=0.0)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    iniciada_at   = Column(DateTime)
    finalizada_at = Column(DateTime)
    creada_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa    = relationship("Empresa",   backref="campanas")
    descuento  = relationship("Descuento", backref="campanas",
                               foreign_keys=[descuento_id])
    creada_por = relationship("Usuario",   backref="campanas_creadas",
                               foreign_keys=[creada_por_id])

    @property
    def tasa_conversion(self) -> float:
        """Porcentaje de destinatarios que reservaron después de la campaña."""
        if not self.total_enviados:
            return 0.0
        return round((self.total_convertidos / self.total_enviados) * 100, 1)

    @property
    def tasa_apertura(self) -> float:
        """Porcentaje de mensajes leídos sobre entregados."""
        if not self.total_entregados:
            return 0.0
        return round((self.total_leidos / self.total_entregados) * 100, 1)

    def __repr__(self):
        return f"<Campana {self.nombre} | {self.estado} | conv:{self.tasa_conversion}%>"