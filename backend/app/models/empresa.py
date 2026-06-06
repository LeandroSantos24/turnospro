"""
models/empresa.py — Modelo Empresa.

Representa cada negocio suscripto a la plataforma.
Es la entidad raíz del sistema multiempresa: todos los demás
registros tienen un empresa_id que los aísla completamente.

Incluye datos de identificación fiscal (CUIT), facturación,
ubicación, branding, redes sociales, configuración operativa
y plan de suscripción SaaS.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text,
    JSON, DateTime, Float, Integer, Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class PlanEmpresa(str, enum.Enum):
    """Planes de suscripción disponibles en la plataforma."""
    FREE       = "free"        # Sin costo, funciones básicas
    BASIC      = "basic"       # Hasta 2 trabajadores
    PRO        = "pro"         # Hasta 10 trabajadores + WhatsApp
    ENTERPRISE = "enterprise"  # Sin límites + soporte prioritario


class CondicionIVA(str, enum.Enum):
    """Condiciones ante el IVA (fiscalidad argentina)."""
    RESPONSABLE_INSCRIPTO = "responsable_inscripto"
    MONOTRIBUTO           = "monotributo"
    EXENTO                = "exento"
    CONSUMIDOR_FINAL      = "consumidor_final"


class Empresa(Base):
    __tablename__ = "empresas"

    # ─── Identificación ───────────────────────────────────────────────────────
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre          = Column(String(100), nullable=False)
    nombre_fantasia = Column(String(100))                  # Nombre visible al público
    rubro           = Column(String(100))                  # barbería, consultorio, etc.
    descripcion     = Column(Text)                         # Descripción del negocio

    # ─── Datos fiscales (Argentina) ───────────────────────────────────────────
    cuit            = Column(String(13))                   # Formato: 20-12345678-9
    razon_social    = Column(String(200))                  # Nombre legal
    condicion_iva   = Column(
        Enum(CondicionIVA),
        default=CondicionIVA.MONOTRIBUTO
    )
    ingresos_brutos = Column(String(20))                   # Número de IIBB

    # ─── Contacto ─────────────────────────────────────────────────────────────
    telefono        = Column(String(20))
    telefono_alt    = Column(String(20))                   # Teléfono alternativo
    email           = Column(String(100))
    whatsapp        = Column(String(20))                   # Número de WhatsApp del negocio

    # ─── Ubicación ────────────────────────────────────────────────────────────
    direccion       = Column(String(255))
    ciudad          = Column(String(100))
    provincia       = Column(String(100))
    codigo_postal   = Column(String(10))
    pais            = Column(String(50), default="Argentina")
    latitud         = Column(Float)                        # Para mostrar en Google Maps
    longitud        = Column(Float)

    # ─── Redes sociales y web ─────────────────────────────────────────────────
    website_url     = Column(String(255))
    instagram_url   = Column(String(255))
    facebook_url    = Column(String(255))
    tiktok_url      = Column(String(255))
    google_maps_url = Column(String(500))

    # ─── Branding ─────────────────────────────────────────────────────────────
    logo_url        = Column(String(500))
    color_primario  = Column(String(7), default="#2563EB")  # Hex, default azul
    color_secundario = Column(String(7), default="#1E3A5F")

    # ─── Configuración operativa ──────────────────────────────────────────────
    zona_horaria             = Column(String(50), default="America/Argentina/Buenos_Aires")
    moneda                   = Column(String(3), default="ARS")
    duracion_turno_default   = Column(Integer, default=30)   # Minutos
    anticipacion_minima_hs   = Column(Integer, default=1)    # Mínimo 1 hora antes
    anticipacion_maxima_dias = Column(Integer, default=30)   # Máximo 30 días antes
    permite_reserva_online   = Column(Boolean, default=True)
    requiere_confirmacion    = Column(Boolean, default=False) # Si el turno necesita confirmación manual
    acepta_pagos_online      = Column(Boolean, default=False)

    # ─── Plan SaaS ────────────────────────────────────────────────────────────
    plan                  = Column(Enum(PlanEmpresa), default=PlanEmpresa.FREE)
    plan_vencimiento      = Column(DateTime)               # Fecha de vencimiento del plan
    max_trabajadores      = Column(Integer, default=1)     # Límite según el plan
    activo                = Column(Boolean, default=True)

    # ─── Configuración extra (JSON flexible) ──────────────────────────────────
    # Para datos adicionales que no justifican una columna propia.
    # Ej: {"dias_no_laborales": ["2024-12-25"], "mensaje_bienvenida": "..."}
    configuracion = Column(JSON, default={})

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    usuarios     = relationship("Usuario",     back_populates="empresa")
    clientes     = relationship("Cliente",     back_populates="empresa")
    trabajadores = relationship("Trabajador",  back_populates="empresa")
    servicios    = relationship("Servicio",    back_populates="empresa")

    def __repr__(self):
        return f"<Empresa {self.nombre} | Plan: {self.plan}>"