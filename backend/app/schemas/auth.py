"""
schemas/auth.py — Schemas de autenticación.

Define la estructura exacta de los datos que entran y salen
de los endpoints de auth. Pydantic valida y serializa automáticamente.
"""

from pydantic import BaseModel, EmailStr, field_validator
from app.security import validate_password_strength


class LoginRequest(BaseModel):
    """Datos requeridos para iniciar sesión."""
    email:    EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@barberia.com",
                "password": "Admin123!"
            }
        }


class TokenResponse(BaseModel):
    """Respuesta al login exitoso — incluye ambos tokens."""
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int          # Segundos hasta que vence el access token
    usuario: dict               # Info básica del usuario logueado


class RefreshRequest(BaseModel):
    """Solicitud de renovación de access token."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Cambio de contraseña por el propio usuario."""
    password_actual: str
    password_nuevo:  str
    password_confirm: str

    @field_validator("password_nuevo")
    @classmethod
    def validar_fortaleza(cls, v: str) -> str:
        ok, msg = validate_password_strength(v)
        if not ok:
            raise ValueError(msg)
        return v

    @field_validator("password_confirm")
    @classmethod
    def passwords_coinciden(cls, v: str, info) -> str:
        if "password_nuevo" in info.data and v != info.data["password_nuevo"]:
            raise ValueError("Las contraseñas no coinciden")
        return v


class ResetPasswordRequest(BaseModel):
    """Solicitud de reset de contraseña (desde email)."""
    token:           str
    password_nuevo:  str
    password_confirm: str

    @field_validator("password_nuevo")
    @classmethod
    def validar_fortaleza(cls, v: str) -> str:
        ok, msg = validate_password_strength(v)
        if not ok:
            raise ValueError(msg)
        return v


class ForgotPasswordRequest(BaseModel):
    """Solicitud de email de recuperación."""
    email: EmailStr