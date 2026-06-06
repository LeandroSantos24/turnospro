"""
models/foto_cliente.py — Fotos de evolución del cliente.

Registra fotos antes/después vinculadas a sesiones o turnos.
Crítico para: estética (facial/corporal), kinesiología,
nutrición (evolución corporal) y cualquier tratamiento visual.

El médico entrevistado confirmó que necesita adjuntar
resultados de estudios (radiografías, análisis) — este mismo
modelo sirve para eso con tipo = ESTUDIO.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TipoFoto(str, enum.Enum):
    ANTES          = "antes"
    DURANTE        = "durante"
    DESPUES        = "despues"
    EVOLUCION      = "evolucion"    # Seguimiento sin antes/después específico
    ESTUDIO        = "estudio"      # Radiografía, análisis, eco, etc.
    REFERENCIA     = "referencia"   # Foto de referencia que trajo el cliente
    TRABAJO        = "trabajo"      # Resultado de un servicio (peluquería, estética)


class FotoCliente(Base):
    __tablename__ = "fotos_clientes"

    # ─── Identificación ───────────────────────────────────────────────────────
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id    = Column(UUID(as_uuid=True), ForeignKey("empresas.id"),     nullable=False)
    cliente_id    = Column(UUID(as_uuid=True), ForeignKey("clientes.id"),     nullable=False)
    turno_id      = Column(UUID(as_uuid=True), ForeignKey("turnos.id"),       nullable=True)
    trabajador_id = Column(UUID(as_uuid=True), ForeignKey("trabajadores.id"), nullable=True)

    # ─── Tipo y clasificación ─────────────────────────────────────────────────
    tipo          = Column(Enum(TipoFoto), nullable=False, default=TipoFoto.EVOLUCION)

    # Zona del cuerpo o área específica fotografiada
    # Ej: "rostro", "abdomen", "espalda", "cabello", "zona lumbar"
    zona          = Column(String(100))

    # Para agrupar fotos de un mismo tratamiento
    # Ej: "Tratamiento criolipólisis - Serie 1"
    grupo         = Column(String(100))

    # Número de sesión dentro del tratamiento
    numero_sesion = Column(Integer)

    # ─── Archivo ──────────────────────────────────────────────────────────────
    url           = Column(String(500), nullable=False)   # URL en el storage
    thumbnail_url = Column(String(500))                   # Versión reducida
    nombre_archivo = Column(String(200))
    tamanio_bytes = Column(Integer)

    # ─── Descripción ──────────────────────────────────────────────────────────
    descripcion   = Column(Text)    # Ej: "Fin de 3ra sesión. Se observa mejora del 40%"

    # ─── Privacidad ───────────────────────────────────────────────────────────
    # Las fotos de evolución pueden ser sensibles
    # solo_staff = True → no visible para el cliente en su portal
    solo_staff    = Column(Boolean, default=True)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa    = relationship("Empresa",    backref="fotos_clientes")
    cliente    = relationship("Cliente",    backref="fotos")
    turno      = relationship("Turno",      backref="fotos")
    trabajador = relationship("Trabajador", backref="fotos_tomadas")

    def __repr__(self):
        return f"<FotoCliente {self.tipo} | {self.zona} | cliente:{self.cliente_id}>"