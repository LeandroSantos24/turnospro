"""
schemas/usuario.py — Schemas de usuarios del sistema.
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from app.models.usuario import RolUsuario
from app.security import validate_password_strength


class UsuarioCreate(BaseModel):
    """Datos para crear un usuario nuevo (solo admin puede hacer esto)."""
    nombre:   str
    apellido: Optional[str] = None
    email:    EmailStr
    password: str
    rol:      RolUsuario = RolUsuario.TRABAJADOR
    telefono: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        ok, msg = validate_password_strength(v)
        if not ok:
            raise ValueError(msg)
        return v


class UsuarioUpdate(BaseModel):
    """Datos actualizables de un usuario."""
    nombre:   Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    foto_url: Optional[str] = None
    activo:   Optional[bool] = None


class UsuarioResponse(BaseModel):
    """Datos del usuario que se devuelven en las respuestas."""
    id:               uuid.UUID
    empresa_id:       uuid.UUID
    nombre:           str
    apellido:         Optional[str]
    email:            str
    rol:              RolUsuario
    activo:           bool
    email_verificado: bool
    ultimo_login:     Optional[datetime]
    created_at:       datetime

    class Config:
        from_attributes = True