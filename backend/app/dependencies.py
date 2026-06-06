"""
dependencies.py — Dependencias compartidas de FastAPI.

Define el sistema de autenticación y autorización que protege
cada endpoint de la API.

Arquitectura de seguridad en capas:
  1. get_db()            → sesión de base de datos
  2. get_current_user()  → valida JWT, retorna usuario
  3. require_*()         → verifica rol y permisos específicos
  4. Aislamiento multi-tenant → empresa_id filtrado automáticamente

Uso en endpoints:
  @router.get("/clientes")
  def list_clientes(
      db: Session = Depends(get_db),
      current_user: Usuario = Depends(require_admin_or_recepcionista)
  ):
      ...
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import SessionLocal
from app.models.usuario import Usuario, RolUsuario
from app.models.empresa import Empresa, PlanEmpresa
from app.security import decode_token


# ─── Esquema de seguridad HTTP Bearer ─────────────────────────────────────────
# FastAPI extrae el token del header: Authorization: Bearer <token>
bearer_scheme = HTTPBearer()


# ─── Sesión de base de datos ──────────────────────────────────────────────────

def get_db():
    """Provee una sesión de DB por request. Siempre se cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Autenticación base ───────────────────────────────────────────────────────

def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Dependencia base de autenticación.
    Extrae y valida el JWT del header Authorization.
    Retorna el usuario autenticado o lanza 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = decode_token(token)

        # Verificamos que sea un access token (no refresh)
        if payload.get("type") != "access":
            raise credentials_exception

        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Buscamos el usuario en la DB
    usuario = db.query(Usuario).filter(
        Usuario.id == user_id,
        Usuario.activo == True
    ).first()

    if not usuario:
        raise credentials_exception

    return usuario


# ─── Dependencias por rol ─────────────────────────────────────────────────────

def require_admin(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Solo administradores.
    Usado para: gestión de empresa, crear usuarios, ver estadísticas,
    configurar integraciones, crear campañas.
    """
    if current_user.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acción reservada para administradores"
        )
    return current_user


def require_admin_or_recepcionista(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Admins y recepcionistas.
    Usado para: gestión de turnos, clientes, pagos básicos.
    """
    if current_user.rol not in [RolUsuario.ADMIN, RolUsuario.RECEPCIONISTA]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenés permiso para realizar esta acción"
        )
    return current_user


def require_any_staff(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Cualquier usuario del staff (admin, recepcionista, trabajador).
    Usado para: ver agenda propia, cargar notas, ver clientes asignados.
    """
    if not current_user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta está desactivada"
        )
    return current_user


# ─── Aislamiento multi-tenant ─────────────────────────────────────────────────

def get_current_empresa(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Empresa:
    """
    Retorna la empresa del usuario autenticado.

    CRÍTICO para multi-tenancy: garantiza que cada usuario
    solo accede a los datos de SU empresa.

    Uso en endpoints que necesitan el objeto empresa completo:
      @router.get("/configuracion")
      def get_config(empresa: Empresa = Depends(get_current_empresa)):
          return empresa.configuracion
    """
    empresa = db.query(Empresa).filter(
        Empresa.id == current_user.empresa_id,
        Empresa.activo == True
    ).first()

    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada o inactiva"
        )
    return empresa


# ─── Control por plan SaaS ────────────────────────────────────────────────────

def require_plan_pro(
    empresa: Empresa = Depends(get_current_empresa)
) -> Empresa:
    """
    Bloquea features premium para empresas en plan FREE.
    Retorna 402 Payment Required con un mensaje claro.
    """
    planes_permitidos = [PlanEmpresa.PRO, PlanEmpresa.ENTERPRISE]
    if empresa.plan not in planes_permitidos:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error":   "feature_no_disponible",
                "mensaje": "Esta función requiere el plan Pro o Enterprise",
                "plan_actual": empresa.plan.value,
                "upgrade_url": "/planes"
            }
        )
    return empresa


def require_plan_enterprise(
    empresa: Empresa = Depends(get_current_empresa)
) -> Empresa:
    """Solo disponible en plan Enterprise."""
    if empresa.plan != PlanEmpresa.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error":   "feature_enterprise",
                "mensaje": "Esta función es exclusiva del plan Enterprise",
                "plan_actual": empresa.plan.value,
                "upgrade_url": "/planes"
            }
        )
    return empresa


def check_trabajador_limit(
    empresa: Empresa = Depends(get_current_empresa),
    db: Session = Depends(get_db),
) -> Empresa:
    """
    Verifica que la empresa no superó el límite de trabajadores de su plan.
    Se usa antes de crear un nuevo trabajador.
    """
    from app.models.trabajador import Trabajador, EstadoTrabajador
    count = db.query(Trabajador).filter(
        Trabajador.empresa_id == empresa.id,
        Trabajador.estado == EstadoTrabajador.ACTIVO
    ).count()

    if empresa.max_trabajadores and count >= empresa.max_trabajadores:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error":   "limite_trabajadores",
                "mensaje": f"Tu plan permite hasta {empresa.max_trabajadores} trabajadores activos",
                "actual":  count,
                "limite":  empresa.max_trabajadores,
                "upgrade_url": "/planes"
            }
        )
    return empresa


# ─── Type aliases para usar en los endpoints ──────────────────────────────────
# Hacen el código más limpio y expresivo

CurrentUser        = Annotated[Usuario, Depends(get_current_user)]
AdminUser          = Annotated[Usuario, Depends(require_admin)]
AdminOrRecep       = Annotated[Usuario, Depends(require_admin_or_recepcionista)]
AnyStaff           = Annotated[Usuario, Depends(require_any_staff)]
CurrentEmpresa     = Annotated[Empresa, Depends(get_current_empresa)]
ProPlan            = Annotated[Empresa, Depends(require_plan_pro)]
EnterprisePlan     = Annotated[Empresa, Depends(require_plan_enterprise)]
DBSession          = Annotated[Session, Depends(get_db)]