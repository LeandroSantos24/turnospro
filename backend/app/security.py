"""
security.py — Funciones de seguridad del sistema.

Centraliza TODO lo relacionado con criptografía:
  - Hashing y verificación de contraseñas (bcrypt directo, sin passlib)
  - Creación y decodificación de tokens JWT
  - Validación de fortaleza de contraseñas
  - Generación de contraseñas temporales y tokens de reset

Separado de la lógica de negocio para poder testearlo
de forma aislada y reemplazar algoritmos sin tocar endpoints.
"""

import re
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as bcrypt_lib
from jose import JWTError, jwt

from app.config import settings


# ─── Contraseñas ──────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """
    Genera un hash bcrypt de la contraseña.
    NUNCA se guarda la contraseña en texto plano — solo este hash.
    rounds=12 es el balance estándar entre seguridad y velocidad.
    """
    salt = bcrypt_lib.gensalt(rounds=12)
    return bcrypt_lib.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara una contraseña en texto plano con su hash bcrypt.
    Retorna True si coinciden, False si no.
    Resistente a timing attacks por diseño de bcrypt.
    """
    return bcrypt_lib.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valida que la contraseña cumpla los requisitos mínimos de seguridad.
    Retorna (es_valida, mensaje_de_error).

    Requisitos:
      - Mínimo 8 caracteres
      - Al menos una mayúscula
      - Al menos una minúscula
      - Al menos un número
      - Al menos un carácter especial
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe tener al menos una mayúscula"
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe tener al menos una minúscula"
    if not re.search(r"\d", password):
        return False, "La contraseña debe tener al menos un número"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-]", password):
        return False, "La contraseña debe tener al menos un carácter especial"
    return True, ""


def generate_temp_password(length: int = 12) -> str:
    """
    Genera una contraseña temporal segura usando el módulo secrets.
    Usada cuando el admin crea un usuario nuevo — se le envía por email.
    secrets es criptográficamente seguro a diferencia de random.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ─── Tokens JWT ───────────────────────────────────────────────────────────────

def create_access_token(
    user_id: str,
    empresa_id: str,
    rol: str,
    empresa_plan: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Crea un JWT de acceso de corta duración (por defecto 60 minutos).

    El payload incluye:
      - sub: ID del usuario (estándar JWT)
      - empresa_id: para aislamiento multi-tenant en cada request
      - rol: para control de acceso basado en roles (RBAC)
      - plan: plan de la empresa (limita features disponibles)
      - type: "access" para diferenciarlo del refresh token
      - exp: timestamp de expiración (validado automáticamente por jose)
      - iat: issued at — cuándo fue emitido
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub":        str(user_id),
        "empresa_id": str(empresa_id),
        "rol":        rol,
        "plan":       empresa_plan,
        "type":       "access",
        "exp":        expire,
        "iat":        datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: str, empresa_id: str) -> str:
    """
    Crea un JWT de refresh de larga duración (7 días).

    El refresh token solo contiene user_id y empresa_id.
    Se usa EXCLUSIVAMENTE para obtener un nuevo access token.
    Si el refresh token vence, el usuario debe loguearse de nuevo.
    No incluye rol ni plan para minimizar el payload.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    payload = {
        "sub":        str(user_id),
        "empresa_id": str(empresa_id),
        "type":       "refresh",
        "exp":        expire,
        "iat":        datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    """
    Decodifica y valida un JWT.
    Lanza JWTError si el token es inválido, expiró o fue manipulado.
    La firma se verifica contra settings.secret_key automáticamente.
    """
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm]
    )


def create_reset_token(user_id: str) -> str:
    """
    Crea un token de un solo uso para resetear contraseña.
    Expira en 1 hora. Se guarda hasheado en la DB para invalidarlo
    después de un solo uso.
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {
        "sub":  str(user_id),
        "type": "password_reset",
        "exp":  expire,
        "iat":  datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)