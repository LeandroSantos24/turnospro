"""
routers/clientes.py — CRUD completo de clientes.

Endpoints:
  POST   /api/v1/clientes              → crear cliente
  GET    /api/v1/clientes              → listar con filtros y paginación
  GET    /api/v1/clientes/buscar       → búsqueda rápida por nombre/teléfono
  GET    /api/v1/clientes/{id}         → detalle completo del cliente
  PATCH  /api/v1/clientes/{id}         → actualizar campos específicos
  DELETE /api/v1/clientes/{id}         → desactivar cliente (soft delete)
  POST   /api/v1/clientes/{id}/nota    → agregar nota interna rápida

Todos los endpoints filtran automáticamente por empresa_id
del usuario autenticado — aislamiento multi-tenant garantizado.
"""

import uuid
import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.dependencies import (
    get_db, get_current_user,
    require_admin_or_recepcionista, require_any_staff,
    DBSession, AdminOrRecep, AnyStaff
)
from app.models.cliente import Cliente, EstadoCliente, NivelFidelizacion
from app.models.usuario import Usuario
from app.schemas.cliente import (
    ClienteCreate, ClienteUpdate,
    ClienteResponse, ClienteListItem, PaginatedClientes
)

router = APIRouter(
    prefix="/api/v1/clientes",
    tags=["clientes"],
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_cliente_o_404(
    cliente_id: uuid.UUID,
    empresa_id: uuid.UUID,
    db: Session
) -> Cliente:
    """
    Busca un cliente por ID filtrando por empresa.
    Lanza 404 si no existe o pertenece a otra empresa.
    Este helper garantiza el aislamiento multi-tenant en todos
    los endpoints que operan sobre un cliente específico.
    """
    cliente = db.query(Cliente).filter(
        Cliente.id == cliente_id,
        Cliente.empresa_id == empresa_id,
    ).first()

    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente {cliente_id} no encontrado"
        )
    return cliente


def actualizar_nivel_fidelizacion(cliente: Cliente) -> None:
    """
    Recalcula el nivel de fidelización según el total de visitas.
    Se llama después de cada turno completado.

    Reglas:
      0-2 visitas  → NUEVO
      3-9 visitas  → REGULAR
      10-24 visitas → FRECUENTE
      25+ visitas  → VIP
    """
    visitas = cliente.total_visitas or 0
    if visitas >= 25:
        cliente.nivel_fidelizacion = NivelFidelizacion.VIP
    elif visitas >= 10:
        cliente.nivel_fidelizacion = NivelFidelizacion.FRECUENTE
    elif visitas >= 3:
        cliente.nivel_fidelizacion = NivelFidelizacion.REGULAR
    else:
        cliente.nivel_fidelizacion = NivelFidelizacion.NUEVO


# ─── POST /clientes — Crear cliente ───────────────────────────────────────────

@router.post(
    "/",
    response_model=ClienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cliente",
    description="Registra un nuevo cliente en la empresa. "
                "El teléfono es el único campo obligatorio además del nombre."
)
def crear_cliente(
    data: ClienteCreate,
    db: DBSession,
    current_user: AdminOrRecep,
):
    """
    Crea un nuevo cliente vinculado a la empresa del usuario autenticado.

    Verifica que no exista otro cliente con el mismo teléfono
    en la misma empresa antes de crearlo.
    """
    # Verificar teléfono duplicado en la misma empresa
    existe = db.query(Cliente).filter(
        Cliente.empresa_id == current_user.empresa_id,
        Cliente.telefono == data.telefono,
    ).first()

    if existe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un cliente con el teléfono {data.telefono}"
        )

    # Crear el cliente con todos los datos recibidos
    cliente = Cliente(
        empresa_id=current_user.empresa_id,
        **data.model_dump(exclude_none=True)
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


# ─── GET /clientes — Listar con filtros y paginación ─────────────────────────

@router.get(
    "/",
    response_model=PaginatedClientes,
    summary="Listar clientes",
    description="Lista todos los clientes de la empresa con filtros opcionales y paginación."
)
def listar_clientes(
    db: DBSession,
    current_user: AnyStaff,
    # Paginación
    pagina:     int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(20, ge=1, le=100, description="Items por página"),
    # Filtros
    estado:             Optional[str] = Query(None, description="Filtrar por estado"),
    nivel_fidelizacion: Optional[str] = Query(None, description="Filtrar por nivel"),
    etiqueta:           Optional[str] = Query(None, description="Filtrar por etiqueta"),
    como_conocio:       Optional[str] = Query(None, description="Canal de adquisición"),
    # Búsqueda
    q: Optional[str] = Query(None, description="Buscar por nombre, apellido o teléfono"),
    # Ordenamiento
    orden_por: str = Query("created_at", description="Campo para ordenar"),
    desc:      bool = Query(True, description="Orden descendente"),
):
    """
    Lista los clientes con soporte de:
    - Búsqueda de texto en nombre, apellido, email y teléfono
    - Filtros por estado, nivel de fidelización, etiqueta y canal de origen
    - Paginación configurable (máx 100 por página)
    - Ordenamiento por cualquier campo
    """
    query = db.query(Cliente).filter(
        Cliente.empresa_id == current_user.empresa_id,
    )

    # Búsqueda de texto
    if q:
        termino = f"%{q.lower()}%"
        query = query.filter(
            or_(
                func.lower(Cliente.nombre).like(termino),
                func.lower(Cliente.apellido).like(termino),
                func.lower(Cliente.email).like(termino),
                Cliente.telefono.like(termino),
            )
        )

    # Filtros exactos
    if estado:
        query = query.filter(Cliente.estado == estado)
    if nivel_fidelizacion:
        query = query.filter(Cliente.nivel_fidelizacion == nivel_fidelizacion)
    if como_conocio:
        query = query.filter(Cliente.como_conocio == como_conocio)

    # Filtro por etiqueta (busca en el JSON array)
    if etiqueta:
        query = query.filter(
            Cliente.etiquetas.contains([etiqueta])
        )

    # Total antes de paginar (para calcular páginas)
    total = query.count()

    # Ordenamiento
    campos_validos = {
        "created_at", "nombre", "apellido",
        "total_visitas", "ultima_visita", "total_gastado"
    }
    if orden_por not in campos_validos:
        orden_por = "created_at"

    col = getattr(Cliente, orden_por)
    query = query.order_by(col.desc() if desc else col.asc())

    # Paginación
    offset = (pagina - 1) * por_pagina
    clientes = query.offset(offset).limit(por_pagina).all()

    return PaginatedClientes(
        items=clientes,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        paginas=math.ceil(total / por_pagina) if total > 0 else 0,
    )


# ─── GET /clientes/buscar — Búsqueda rápida ───────────────────────────────────

@router.get(
    "/buscar",
    response_model=list[ClienteListItem],
    summary="Búsqueda rápida",
    description="Retorna los primeros 10 resultados que coincidan. "
                "Ideal para autocomplete al asignar un turno."
)
def buscar_clientes(
    q: str = Query(..., min_length=2, description="Término de búsqueda (mín. 2 caracteres)"),
    db: DBSession = None,
    current_user: AnyStaff = None,
):
    """
    Búsqueda rápida para usar en autocomplete.
    Busca en nombre, apellido, email y teléfono.
    Retorna máximo 10 resultados ordenados por nombre.
    """
    termino = f"%{q.lower()}%"
    clientes = db.query(Cliente).filter(
        Cliente.empresa_id == current_user.empresa_id,
        Cliente.estado != EstadoCliente.BLOQUEADO,
        or_(
            func.lower(Cliente.nombre).like(termino),
            func.lower(Cliente.apellido).like(termino),
            func.lower(Cliente.email).like(termino),
            Cliente.telefono.like(termino),
        )
    ).order_by(Cliente.nombre).limit(10).all()

    return clientes


# ─── GET /clientes/{id} — Detalle completo ────────────────────────────────────

@router.get(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Obtener cliente",
    description="Retorna el perfil completo del cliente con todos sus datos CRM."
)
def obtener_cliente(
    cliente_id: uuid.UUID,
    db: DBSession,
    current_user: AnyStaff,
):
    return get_cliente_o_404(cliente_id, current_user.empresa_id, db)


# ─── PATCH /clientes/{id} — Actualizar parcialmente ──────────────────────────

@router.patch(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Actualizar cliente",
    description="Actualiza solo los campos enviados. Los campos no incluidos no se modifican."
)
def actualizar_cliente(
    cliente_id: uuid.UUID,
    data: ClienteUpdate,
    db: DBSession,
    current_user: AdminOrRecep,
):
    """
    Actualización parcial (PATCH semántico).
    Solo modifica los campos que vienen en el body.
    Los campos con valor None en el body no se actualizan.

    Ejemplo: enviar {"nombre": "Juan Carlos"} solo cambia el nombre,
    dejando todos los demás campos intactos.
    """
    cliente = get_cliente_o_404(cliente_id, current_user.empresa_id, db)

    # Obtenemos solo los campos que vinieron en el request (excluimos None)
    campos = data.model_dump(exclude_none=True)

    if not campos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos para actualizar"
        )

    # Aplicamos cada campo al objeto
    for campo, valor in campos.items():
        setattr(cliente, campo, valor)

    # Si se actualizó el nivel de fidelización manualmente, lo respetamos.
    # Si no, recalculamos automáticamente.
    if "nivel_fidelizacion" not in campos:
        actualizar_nivel_fidelizacion(cliente)

    cliente.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cliente)
    return cliente


# ─── DELETE /clientes/{id} — Soft delete ──────────────────────────────────────

@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_200_OK,
    summary="Desactivar cliente",
    description="Desactiva el cliente (soft delete). "
                "El historial y los turnos anteriores se conservan."
)
def desactivar_cliente(
    cliente_id: uuid.UUID,
    db: DBSession,
    current_user: AdminOrRecep,
):
    """
    Soft delete — no borra físicamente el cliente de la base de datos.

    Por qué soft delete y no DELETE real:
    El cliente puede tener turnos pasados, pagos y calificaciones asociadas.
    Borrarlo rompe la integridad referencial y pierde el historial del negocio.
    En su lugar, lo marcamos como BLOQUEADO para que no aparezca en búsquedas
    pero el historial queda intacto.
    """
    cliente = get_cliente_o_404(cliente_id, current_user.empresa_id, db)

    if cliente.estado == EstadoCliente.BLOQUEADO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cliente ya está desactivado"
        )

    cliente.estado = EstadoCliente.BLOQUEADO
    cliente.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "mensaje": f"Cliente {cliente.nombre} desactivado correctamente",
        "id": str(cliente_id)
    }


# ─── POST /clientes/{id}/nota — Agregar nota interna rápida ──────────────────

@router.post(
    "/{cliente_id}/nota",
    response_model=ClienteResponse,
    summary="Agregar nota interna",
    description="Agrega o reemplaza la nota interna del cliente. "
                "Solo visible para el staff, nunca para el cliente."
)
def agregar_nota(
    cliente_id: uuid.UUID,
    nota: str = Query(..., min_length=1, max_length=1000),
    db: DBSession = None,
    current_user: AnyStaff = None,
):
    """
    Endpoint rápido para que el trabajador agregue una nota
    después de atender al cliente sin tener que abrir el perfil completo.

    Ejemplo de uso: el barbero termina el corte y anota
    "Le hice degradado con tijera, prefiere no usar máquina en los costados"
    """
    cliente = get_cliente_o_404(cliente_id, current_user.empresa_id, db)
    cliente.notas_ultimo_servicio = nota
    cliente.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cliente)
    return cliente