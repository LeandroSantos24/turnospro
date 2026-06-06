"""
services/auth_service.py — Lógica de negocio de autenticación.

Separa la lógica del endpoint (router) de la lógica de negocio.
El router solo recibe el request y llama al service.
El service interactúa con la DB y aplica las reglas.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.config import settings


def authenticate_user(db: Session, email: str, password: str) -> Usuario:
    """
    Verifica email y contraseña. Retorna el usuario si son correctos.
    Mismo mensaje para email y password incorrectos — no revela cuál falló.
    """
    usuario = db.query(Usuario).filter(
        Usuario.email == email,
    ).first()

    if not usuario or not verify_password(password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta está desactivada. Contactá al administrador."
        )

    return usuario


def create_user_tokens(usuario: Usuario, db: Session) -> dict:
    """
    Genera el par de tokens (access + refresh) para un usuario autenticado.
    También actualiza el campo ultimo_login del usuario.

    Incluye el plan de la empresa en el token para que el frontend
    pueda mostrar/ocultar features sin hacer requests extra.
    """
    empresa = db.query(Empresa).filter(Empresa.id == usuario.empresa_id).first()
    plan = empresa.plan.value if empresa else "free"

    access_token = create_access_token(
        user_id=str(usuario.id),
        empresa_id=str(usuario.empresa_id),
        rol=usuario.rol.value,
        empresa_plan=plan,
    )
    refresh_token = create_refresh_token(
        user_id=str(usuario.id),
        empresa_id=str(usuario.empresa_id),
    )

    # Registramos el último login
    usuario.ultimo_login = datetime.now(timezone.utc)
    db.commit()

    return {
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "token_type":    "bearer",
        "expires_in":    settings.access_token_expire_minutes * 60,
        "usuario": {
            "id":       str(usuario.id),
            "nombre":   usuario.nombre,
            "apellido": usuario.apellido,
            "email":    usuario.email,
            "rol":      usuario.rol.value,
            "plan":     plan,
        }
    }


def refresh_access_token(refresh_token: str, db: Session) -> dict:
    """
    Valida el refresh token y emite un nuevo access token.

    El frontend llama a este endpoint cuando recibe un 401
    en cualquier endpoint protegido — así el usuario no tiene
    que loguearse de nuevo cada 60 minutos.
    """
    from jose import JWTError

    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token inválido o expirado"
    )

    try:
        payload = decode_token(refresh_token)

        # Verificamos que sea un refresh token (no un access token)
        if payload.get("type") != "refresh":
            raise error

        user_id = payload.get("sub")
        if not user_id:
            raise error

    except JWTError:
        raise error

    usuario = db.query(Usuario).filter(
        Usuario.id == user_id,
        Usuario.activo == True
    ).first()

    if not usuario:
        raise error

    return create_user_tokens(usuario, db)