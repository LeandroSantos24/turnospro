"""
models/cliente.py — Modelo Cliente (CRM completo).

Representa a la persona que recibe el servicio.
Es el modelo más rico del sistema: centraliza datos personales,
físicos, familiares, preferencias, observaciones internas,
fidelización y estadísticas de visitas.

Todo lo que un negocio necesita para conocer realmente a su cliente
y brindarle una atención personalizada.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text, Integer,
    DateTime, Float, Date, Enum, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class GeneroCliente(str, enum.Enum):
    MASCULINO   = "masculino"
    FEMENINO    = "femenino"
    NO_BINARIO  = "no_binario"
    PREFIERO_NO = "prefiero_no_decir"


class EstadoCliente(str, enum.Enum):
    ACTIVO   = "activo"     # Cliente recurrente normal
    INACTIVO = "inactivo"   # Sin visitas hace más de 60 días
    NUEVO    = "nuevo"      # Primera visita aún no realizada
    BLOQUEADO = "bloqueado" # Bloqueado por el negocio (no-shows repetidos, etc.)


class NivelFidelizacion(str, enum.Enum):
    NUEVO     = "nuevo"      # 0-2 visitas
    REGULAR   = "regular"    # 3-9 visitas
    FRECUENTE = "frecuente"  # 10-24 visitas
    VIP       = "vip"        # 25+ visitas o alto gasto


class ComoConocio(str, enum.Enum):
    """Fuente de adquisición del cliente."""
    INSTAGRAM   = "instagram"
    FACEBOOK    = "facebook"
    GOOGLE      = "google"
    REFERIDO    = "referido"       # Lo trajo otro cliente
    PASANDO     = "pasando"        # Pasó por la puerta
    WHATSAPP    = "whatsapp"
    OTRO        = "otro"


class Cliente(Base):
    __tablename__ = "clientes"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)

    # ─── Datos personales básicos ─────────────────────────────────────────────
    nombre          = Column(String(100), nullable=False)
    apellido        = Column(String(100))
    email           = Column(String(100))
    telefono        = Column(String(20), nullable=False)
    telefono_alt    = Column(String(20))
    fecha_nacimiento = Column(Date)                       # Para mensajes de cumpleaños
    genero          = Column(Enum(GeneroCliente))
    dni             = Column(String(15))                  # DNI argentino
    foto_url        = Column(String(500))
    direccion       = Column(String(255))

    # ─── Datos físicos / características ──────────────────────────────────────
    # Muy útiles para barberías, peluquerías y centros de estética.
    # El trabajador los completa en la primera visita.
    tipo_cabello         = Column(String(50))     # liso, rizado, ondulado, afro
    color_cabello_natural = Column(String(50))    # rubio, castaño, negro, etc.
    color_cabello_actual = Column(String(100))    # color actual con tinte
    largo_cabello        = Column(String(30))     # corto, medio, largo
    tipo_piel            = Column(String(50))     # seca, grasa, mixta, sensible
    alergias             = Column(Text)           # IMPORTANTE: alergias a productos
    medicamentos         = Column(Text)           # Medicamentos que afecten tratamientos

    # ─── Vida personal ────────────────────────────────────────────────────────
    # Datos para personalizar la atención y generar conexión real.
    ocupacion          = Column(String(100))
    es_padre_madre     = Column(Boolean)
    cantidad_hijos     = Column(Integer)
    # JSON para recordar nombres y edades de los hijos
    # Ej: [{"nombre": "Mateo", "edad": 5}, {"nombre": "Valentina", "edad": 8}]
    hijos              = Column(JSON, default=[])
    estado_civil       = Column(String(30))       # soltero, casado, en pareja, etc.
    nombre_pareja      = Column(String(100))      # Para preguntar por él/ella
    fecha_aniversario  = Column(Date)             # Para enviar promoción especial
    intereses          = Column(JSON, default=[]) # ["fútbol", "música", "viajes"]
    mascota            = Column(String(100))      # Nombre y tipo de mascota

    # ─── Preferencias de servicio ─────────────────────────────────────────────
    trabajador_preferido_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trabajadores.id"),
        nullable=True
    )
    horario_preferido  = Column(String(20))   # mañana, tarde, noche
    dia_preferido      = Column(String(20))   # lunes, martes, etc.

    # ─── Preferencias de comunicación ────────────────────────────────────────
    canal_preferido       = Column(String(20), default="whatsapp")  # whatsapp, email, sms
    acepta_promociones    = Column(Boolean, default=True)
    acepta_recordatorios  = Column(Boolean, default=True)
    acepta_cumpleanos     = Column(Boolean, default=True)

    # ─── Origen / adquisición ────────────────────────────────────────────────
    como_conocio           = Column(Enum(ComoConocio))
    referido_por_id        = Column(
        UUID(as_uuid=True),
        ForeignKey("clientes.id"),
        nullable=True
    )

    # ─── CRM — Notas e información interna ───────────────────────────────────
    # observaciones_internas: SOLO visible para el equipo, nunca al cliente.
    # Ej: "Le gusta el café mientras espera", "Es muy puntual", "Prefiere música tranquila"
    observaciones_internas = Column(Text)

    # notas_ultimo_servicio: se actualiza después de cada visita
    notas_ultimo_servicio  = Column(Text)

    # Etiquetas para segmentar clientes
    # Ej: ["vip", "referente", "puntual", "sensible_precio"]
    etiquetas              = Column(JSON, default=[])

    # ─── Fidelización ─────────────────────────────────────────────────────────
    nivel_fidelizacion = Column(
        Enum(NivelFidelizacion),
        default=NivelFidelizacion.NUEVO
    )
    puntos_fidelizacion = Column(Integer, default=0)  # Sistema de puntos

    # ─── Estadísticas de visitas (se actualizan automáticamente) ─────────────
    primera_visita  = Column(DateTime)
    ultima_visita   = Column(DateTime)
    total_visitas   = Column(Integer, default=0)
    total_gastado   = Column(Float, default=0.0)         # Gasto histórico en ARS
    ausencias       = Column(Integer, default=0)         # Veces que no vino sin avisar

    # ─── Estado ───────────────────────────────────────────────────────────────
    estado = Column(Enum(EstadoCliente), default=EstadoCliente.NUEVO)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa             = relationship("Empresa",    back_populates="clientes")
    trabajador_preferido = relationship("Trabajador", foreign_keys=[trabajador_preferido_id])
    referido_por        = relationship("Cliente",    foreign_keys=[referido_por_id], remote_side="Cliente.id")
    turnos              = relationship("Turno",      back_populates="cliente")

    def __repr__(self):
        return f"<Cliente {self.nombre} {self.apellido} | {self.nivel_fidelizacion}>"