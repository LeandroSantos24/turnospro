"""
routers/auth.py — Endpoints de autenticación.

POST /api/v1/auth/login          → login con email/password
POST /api/v1/auth/refresh        → renovar access token
POST /api/v1/auth/logout         → logout (invalidar sesión)
GET  /api/v1/auth/me             → datos del usuario actual
POST /api/v1/auth/change-password → cambiar contraseña
POST /api/v1/auth/forgot-password → solicitar reset por email
POST /api/v1/auth/reset-password  → resetear con token del email
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, DBSession, CurrentUser
from app.schemas.auth import (
    LoginRequest, TokenResponse, RefreshRequest,
    ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest
)
from app.schemas.usuario import UsuarioResponse
from app.services.auth_service import (
    authenticate_user, create_user_tokens, refresh_access_token
)
from app.security import verify_password, hash_password, decode_token
from app.models.usuario import Usuario

router = APIRouter(prefix="/api/v1/auth", tags=["autenticación"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: DBSession):
    """
    Autentica al usuario y retorna los tokens JWT.

    El access token dura 60 minutos.
    El refresh token dura 7 días.

    Incluye en la respuesta los datos básicos del usuario
    para que el frontend no tenga que hacer un request extra.
    """
    usuario = authenticate_user(db, request.email, request.password)
    return create_user_tokens(usuario, db)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest, db: DBSession):
    """
    Renueva el access token usando el refresh token.

    El frontend debe llamar a este endpoint cuando recibe
    un 401 en cualquier endpoint protegido.
    """
    return refresh_access_token(request.refresh_token, db)


@router.get("/me", response_model=UsuarioResponse)
def get_me(current_user: CurrentUser):
    """
    Retorna los datos del usuario actualmente autenticado.
    Útil para que el frontend verifique la sesión al arrancar.
    """
    return current_user


@router.post("/logout")
def logout(current_user: CurrentUser):
    """
    Cierra la sesión del usuario.

    En esta implementación el logout es del lado del cliente
    (el frontend descarta los tokens). En una implementación
    avanzada se podría usar una blacklist de tokens en Redis.
    """
    return {
        "mensaje": f"Hasta luego, {current_user.nombre}",
        "status":  "logged_out"
    }


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Permite al usuario cambiar su propia contraseña.
    Requiere la contraseña actual como confirmación de identidad.
    """
    # Verificamos la contraseña actual
    if not verify_password(request.password_actual, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta"
        )

    # Actualizamos el hash
    current_user.password_hash = hash_password(request.password_nuevo)
    db.commit()

    return {"mensaje": "Contraseña actualizada correctamente"}


@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: DBSession):
    """
    Envía un email con link de recuperación de contraseña.

    Siempre retorna el mismo mensaje aunque el email no exista
    para no revelar si un email está registrado (seguridad).
    """
    from app.security import create_reset_token
    from datetime import datetime, timezone

    usuario = db.query(Usuario).filter(
        Usuario.email == request.email
    ).first()

    if usuario:
        token = create_reset_token(str(usuario.id))
        # Guardamos el token en la DB para poder validarlo
        usuario.token_reset = token
        from datetime import timedelta
        usuario.token_reset_exp = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()

        # TODO: Enviar email con el link de reset
        # email_service.send_reset_email(usuario.email, token)

    # Siempre retornamos el mismo mensaje
    return {
        "mensaje": "Si ese email está registrado, recibirás las instrucciones en breve"
    }


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: DBSession):
    """
    Establece una nueva contraseña usando el token del email.
    El token tiene validez de 1 hora.
    """
    from jose import JWTError
    from datetime import datetime, timezone

    try:
        payload = decode_token(request.token)
        if payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido"
            )
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado"
        )

    usuario = db.query(Usuario).filter(
        Usuario.id == user_id,
        Usuario.token_reset == request.token,
        Usuario.activo == True
    ).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o ya utilizado"
        )

    # Verificamos que no haya expirado en la DB también
    if usuario.token_reset_exp and usuario.token_reset_exp < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token expiró. Solicitá uno nuevo."
        )

    # Actualizamos la contraseña y limpiamos el token
    usuario.password_hash = hash_password(request.password_nuevo)
    usuario.token_reset    = None
    usuario.token_reset_exp = None
    db.commit()

    return {"mensaje": "Contraseña restablecida correctamente. Ya podés iniciar sesión."}