"""
routers/servicios.py — CRUD de categorías y servicios.

Endpoints categorías:
  POST   /api/v1/servicios/categorias         → crear categoría
  GET    /api/v1/servicios/categorias         → listar categorías
  PATCH  /api/v1/servicios/categorias/{id}    → actualizar categoría
  DELETE /api/v1/servicios/categorias/{id}    → desactivar categoría

Endpoints servicios:
  POST   /api/v1/servicios                    → crear servicio
  GET    /api/v1/servicios                    → listar servicios
  GET    /api/v1/servicios/{id}               → detalle del servicio
  PATCH  /api/v1/servicios/{id}               → actualizar servicio
  DELETE /api/v1/servicios/{id}               → desactivar servicio
  POST   /api/v1/servicios/{id}/trabajadores  → asignar trabajadores al servicio
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import DBSession, AdminUser, AnyStaff
from app.models.categoria import Categoria
from app.models.servicio import Servicio
from app.models.trabajador import Trabajador
from app.schemas.servicio import (
    CategoriaCreate, CategoriaResponse,
    ServicioCreate, ServicioUpdate, ServicioResponse
)

router = APIRouter(
    prefix="/api/v1/servicios",
    tags=["servicios"],
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_servicio_o_404(servicio_id: uuid.UUID, empresa_id: uuid.UUID, db: Session) -> Servicio:
    s = db.query(Servicio).filter(
        Servicio.id == servicio_id,
        Servicio.empresa_id == empresa_id,
    ).first()
    if not s:
        raise HTTPException(status_code=404, detail=f"Servicio {servicio_id} no encontrado")
    return s


def get_categoria_o_404(categoria_id: uuid.UUID, empresa_id: uuid.UUID, db: Session) -> Categoria:
    c = db.query(Categoria).filter(
        Categoria.id == categoria_id,
        Categoria.empresa_id == empresa_id,
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Categoría {categoria_id} no encontrada")
    return c


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORÍAS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/categorias",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear categoría",
)
def crear_categoria(data: CategoriaCreate, db: DBSession, current_user: AdminUser):
    """
    Crea una categoría para agrupar servicios.
    Ejemplos: Cortes, Barba, Color, Tratamientos, Faciales.
    """
    categoria = Categoria(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.get(
    "/categorias",
    response_model=list[CategoriaResponse],
    summary="Listar categorías",
)
def listar_categorias(db: DBSession, current_user: AnyStaff):
    """Lista las categorías activas ordenadas por orden_display."""
    return db.query(Categoria).filter(
        Categoria.empresa_id == current_user.empresa_id,
        Categoria.activo == True,
    ).order_by(Categoria.orden_display, Categoria.nombre).all()


@router.patch(
    "/categorias/{categoria_id}",
    response_model=CategoriaResponse,
    summary="Actualizar categoría",
)
def actualizar_categoria(
    categoria_id: uuid.UUID,
    data: CategoriaCreate,
    db: DBSession,
    current_user: AdminUser,
):
    categoria = get_categoria_o_404(categoria_id, current_user.empresa_id, db)
    for campo, valor in data.model_dump(exclude_none=True).items():
        setattr(categoria, campo, valor)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/categorias/{categoria_id}", summary="Desactivar categoría")
def desactivar_categoria(
    categoria_id: uuid.UUID,
    db: DBSession,
    current_user: AdminUser,
):
    categoria = get_categoria_o_404(categoria_id, current_user.empresa_id, db)
    categoria.activo = False
    db.commit()
    return {"mensaje": f"Categoría {categoria.nombre} desactivada"}


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICIOS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/",
    response_model=ServicioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear servicio",
)
def crear_servicio(data: ServicioCreate, db: DBSession, current_user: AdminUser):
    """
    Crea un servicio del negocio.
    El campo precio_vigente se calcula automáticamente:
    si hay precio_descuento, ese es el vigente; si no, el precio base.
    """
    # Verificamos que la categoría pertenezca a la empresa
    if data.categoria_id:
        get_categoria_o_404(data.categoria_id, current_user.empresa_id, db)

    servicio = Servicio(
        empresa_id=current_user.empresa_id,
        **data.model_dump(exclude_none=True)
    )
    db.add(servicio)
    db.commit()
    db.refresh(servicio)
    return servicio


@router.get(
    "/",
    response_model=list[ServicioResponse],
    summary="Listar servicios",
)
def listar_servicios(
    db: DBSession,
    current_user: AnyStaff,
    solo_activos: bool     = Query(True),
    categoria_id: Optional[uuid.UUID] = Query(None),
    solo_online:  bool     = Query(False, description="Solo servicios disponibles para reserva online"),
):
    """
    Lista servicios con filtros opcionales.
    Ordenados por destacado primero, luego por orden_display.
    """
    query = db.query(Servicio).filter(
        Servicio.empresa_id == current_user.empresa_id
    )
    if solo_activos:
        query = query.filter(Servicio.activo == True)
    if categoria_id:
        query = query.filter(Servicio.categoria_id == categoria_id)
    if solo_online:
        query = query.filter(
            Servicio.visible_online == True,
            Servicio.permite_reserva_online == True,
        )

    return query.order_by(
        Servicio.destacado.desc(),
        Servicio.orden_display,
        Servicio.nombre,
    ).all()


@router.get(
    "/{servicio_id}",
    response_model=ServicioResponse,
    summary="Obtener servicio",
)
def obtener_servicio(
    servicio_id: uuid.UUID,
    db: DBSession,
    current_user: AnyStaff,
):
    return get_servicio_o_404(servicio_id, current_user.empresa_id, db)


@router.patch(
    "/{servicio_id}",
    response_model=ServicioResponse,
    summary="Actualizar servicio",
)
def actualizar_servicio(
    servicio_id: uuid.UUID,
    data: ServicioUpdate,
    db: DBSession,
    current_user: AdminUser,
):
    """
    Actualiza el servicio. Si se envía trabajador_ids,
    reemplaza la lista completa de trabajadores asignados.
    """
    servicio = get_servicio_o_404(servicio_id, current_user.empresa_id, db)

    campos = data.model_dump(exclude_none=True)
    trabajador_ids = campos.pop("trabajador_ids", None)

    for campo, valor in campos.items():
        setattr(servicio, campo, valor)

    # Reasignamos trabajadores si se enviaron
    if trabajador_ids is not None:
        trabajadores = db.query(Trabajador).filter(
            Trabajador.id.in_(trabajador_ids),
            Trabajador.empresa_id == current_user.empresa_id,
        ).all()

        if len(trabajadores) != len(trabajador_ids):
            raise HTTPException(
                status_code=400,
                detail="Uno o más trabajadores no existen en esta empresa"
            )
        servicio.trabajadores = trabajadores

    servicio.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(servicio)
    return servicio


@router.delete("/{servicio_id}", summary="Desactivar servicio")
def desactivar_servicio(
    servicio_id: uuid.UUID,
    db: DBSession,
    current_user: AdminUser,
):
    """
    Desactiva el servicio. No borra los turnos pasados.
    El servicio no aparecerá más en el catálogo ni en reservas online.
    """
    servicio = get_servicio_o_404(servicio_id, current_user.empresa_id, db)
    servicio.activo = False
    servicio.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"mensaje": f"Servicio {servicio.nombre} desactivado"}


@router.post(
    "/{servicio_id}/trabajadores",
    response_model=ServicioResponse,
    summary="Asignar trabajadores al servicio",
)
def asignar_trabajadores(
    servicio_id: uuid.UUID,
    trabajador_ids: List[uuid.UUID],
    db: DBSession,
    current_user: AdminUser,
):
    """
    Asigna qué trabajadores pueden realizar este servicio.
    Reemplaza la lista completa — enviá todos los que querés asignar.

    Ejemplo: el servicio "Coloración" solo lo puede hacer
    la trabajadora especializada, no todos los barberos.
    """
    servicio = get_servicio_o_404(servicio_id, current_user.empresa_id, db)

    trabajadores = db.query(Trabajador).filter(
        Trabajador.id.in_(trabajador_ids),
        Trabajador.empresa_id == current_user.empresa_id,
    ).all()

    if len(trabajadores) != len(trabajador_ids):
        raise HTTPException(
            status_code=400,
            detail="Uno o más trabajadores no existen en esta empresa"
        )

    servicio.trabajadores = trabajadores
    servicio.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(servicio)
    return servicio