"""
models/ficha_clinica.py — Ficha clínica/especializada por vertical.

Extiende la información del Cliente con datos específicos
del rubro del negocio. Usa JSONB para ser flexible:
cada negocio define los campos que necesita.

Plantillas predefinidas por vertical:
  - NUTRICION:     obra social, peso, talla, plan alimentario
  - KINESIOLOGIA:  diagnóstico, zona tratada, ejercicios
  - PSICOLOGIA:    motivo consulta, obra social, notas sesión
  - ODONTOLOGIA:   obra social, historial dental, presupuesto
  - VETERINARIA:   mascota, vacunas, medicación
  - PERSONALIZADO: el negocio define sus propios campos

Esta arquitectura permite escalar a cualquier vertical
sin cambiar el esquema de la base de datos.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Text,
    DateTime, Enum, ForeignKey, JSON, Integer
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TipoFicha(str, enum.Enum):
    NUTRICION     = "nutricion"
    KINESIOLOGIA  = "kinesiologia"
    PSICOLOGIA    = "psicologia"
    ODONTOLOGIA   = "odontologia"
    MEDICINA      = "medicina"
    VETERINARIA   = "veterinaria"
    FITNESS       = "fitness"
    PERSONALIZADO = "personalizado"


# ─── Plantillas de campos por vertical ───────────────────────────────────────
# Define qué campos aparecen en el formulario según el tipo de negocio.
# El frontend usa esto para renderizar el formulario dinámicamente.
PLANTILLAS_FICHA = {
    TipoFicha.NUTRICION: {
        "campos": [
            {"clave": "obra_social",       "label": "Obra social / prepaga", "tipo": "text"},
            {"clave": "numero_afiliado",   "label": "N° de afiliado",        "tipo": "text"},
            {"clave": "peso_kg",           "label": "Peso (kg)",             "tipo": "number"},
            {"clave": "talla_cm",          "label": "Talla (cm)",            "tipo": "number"},
            {"clave": "objetivo",          "label": "Objetivo",              "tipo": "select",
             "opciones": ["bajar de peso", "ganar músculo", "mantenimiento", "salud general"]},
            {"clave": "alergias_alim",     "label": "Alergias alimentarias", "tipo": "text"},
            {"clave": "intolerancias",     "label": "Intolerancias",         "tipo": "text"},
            {"clave": "patologias",        "label": "Patologías",            "tipo": "text"},
            {"clave": "medicacion",        "label": "Medicación actual",     "tipo": "text"},
            {"clave": "actividad_fisica",  "label": "Actividad física",      "tipo": "select",
             "opciones": ["sedentario", "leve", "moderado", "intenso"]},
            {"clave": "plan_actual",       "label": "Plan alimentario actual","tipo": "textarea"},
        ]
    },
    TipoFicha.KINESIOLOGIA: {
        "campos": [
            {"clave": "obra_social",       "label": "Obra social",           "tipo": "text"},
            {"clave": "diagnostico",       "label": "Diagnóstico",           "tipo": "textarea"},
            {"clave": "zona_tratada",      "label": "Zona tratada",          "tipo": "text"},
            {"clave": "medico_derivante",  "label": "Médico derivante",      "tipo": "text"},
            {"clave": "sesiones_indicadas","label": "Sesiones indicadas",    "tipo": "number"},
            {"clave": "ejercicios",        "label": "Ejercicios indicados",  "tipo": "textarea"},
            {"clave": "observaciones",     "label": "Observaciones",         "tipo": "textarea"},
        ]
    },
    TipoFicha.PSICOLOGIA: {
        "campos": [
            {"clave": "obra_social",       "label": "Obra social",           "tipo": "text"},
            {"clave": "motivo_consulta",   "label": "Motivo de consulta",    "tipo": "textarea"},
            {"clave": "derivado_por",      "label": "Derivado por",          "tipo": "text"},
            {"clave": "frecuencia",        "label": "Frecuencia indicada",   "tipo": "select",
             "opciones": ["semanal", "quincenal", "mensual"]},
            {"clave": "medicacion",        "label": "Medicación actual",     "tipo": "text"},
            {"clave": "antecedentes",      "label": "Antecedentes relevantes","tipo": "textarea"},
        ]
    },
    TipoFicha.VETERINARIA: {
        "campos": [
            {"clave": "nombre_mascota",    "label": "Nombre de la mascota",  "tipo": "text"},
            {"clave": "especie",           "label": "Especie",               "tipo": "select",
             "opciones": ["perro", "gato", "ave", "conejo", "otro"]},
            {"clave": "raza",              "label": "Raza",                  "tipo": "text"},
            {"clave": "edad_mascota",      "label": "Edad",                  "tipo": "text"},
            {"clave": "peso_mascota",      "label": "Peso (kg)",             "tipo": "number"},
            {"clave": "vacunas",           "label": "Vacunas al día",        "tipo": "select",
             "opciones": ["sí", "no", "parcial"]},
            {"clave": "medicacion",        "label": "Medicación actual",     "tipo": "text"},
            {"clave": "alergias",          "label": "Alergias conocidas",    "tipo": "text"},
        ]
    },
    TipoFicha.FITNESS: {
        "campos": [
            {"clave": "objetivo",          "label": "Objetivo",              "tipo": "select",
             "opciones": ["fuerza", "cardio", "pérdida de peso", "tonificación", "rendimiento"]},
            {"clave": "nivel",             "label": "Nivel",                 "tipo": "select",
             "opciones": ["principiante", "intermedio", "avanzado"]},
            {"clave": "peso_kg",           "label": "Peso (kg)",             "tipo": "number"},
            {"clave": "lesiones",          "label": "Lesiones o limitaciones","tipo": "text"},
            {"clave": "dias_semana",       "label": "Días por semana",       "tipo": "number"},
            {"clave": "rutina_actual",     "label": "Rutina actual",         "tipo": "textarea"},
        ]
    },
}


class FichaClinica(Base):
    __tablename__ = "fichas_clinicas"

    # ─── Identificación ───────────────────────────────────────────────────────
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"),  nullable=False)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"),  nullable=False, unique=True)

    # ─── Tipo de ficha ────────────────────────────────────────────────────────
    tipo_ficha = Column(Enum(TipoFicha), nullable=False, default=TipoFicha.PERSONALIZADO)

    # ─── Datos clínicos (JSONB para búsquedas eficientes) ─────────────────────
    # Estructura libre según el tipo de ficha.
    # Ej nutricionista: {"peso_kg": 75, "obra_social": "OSDE", "objetivo": "bajar de peso"}
    # Ej kinesiología:  {"diagnostico": "Lumbalgia L4-L5", "sesiones_indicadas": 12}
    datos = Column(JSONB, default={})

    # ─── Historial de evolución ───────────────────────────────────────────────
    # Registro cronológico de mediciones y cambios.
    # Ej: [{"fecha": "2024-01-15", "peso_kg": 80, "nota": "Inicio del plan"}]
    historial_evolución = Column(JSONB, default=[])

    # ─── Campos personalizados extra ─────────────────────────────────────────
    # Para campos que el negocio agrega más allá de la plantilla
    campos_extra = Column(JSONB, default={})

    # ─── Control ──────────────────────────────────────────────────────────────
    ultima_actualizacion_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # ─── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relaciones ───────────────────────────────────────────────────────────
    empresa  = relationship("Empresa", backref="fichas_clinicas")
    cliente  = relationship("Cliente", backref="ficha_clinica", uselist=False)
    actualizado_por = relationship("Usuario", backref="fichas_actualizadas",
                                    foreign_keys=[ultima_actualizacion_por])

    def agregar_evolucion(self, datos_nueva_medicion: dict):
        """
        Agrega una nueva entrada al historial de evolución.
        Ej: ficha.agregar_evolucion({"peso_kg": 73, "nota": "Bajó 2kg este mes"})
        """
        entrada = {"fecha": datetime.utcnow().isoformat(), **datos_nueva_medicion}
        if self.historial_evolución is None:
            self.historial_evolución = []
        self.historial_evolución = [*self.historial_evolución, entrada]

    def __repr__(self):
        return f"<FichaClinica {self.tipo_ficha} | cliente:{self.cliente_id}>"