"""
routers/trabajadores.py — CRUD de trabajadores.

Endpoints:
  POST   /api/v1/trabajadores          → crear trabajador
  GET    /api/v1/trabajadores          → listar trabajadores activos
  GET    /api/v1/trabajadores/{id}     → detalle del trabajador
  PATCH  /api/v1/trabajadores/{id}     → actualizar datos
  DELETE /api/v1/trabajadores/{id}     → desactivar (soft delete)
  GET    /api/v1/trabajadores/{id}/disponibilidad → horarios libres en una fecha

Solo el ADMIN puede crear, editar y desactivar trabajadores.
Cualquier staff puede ver el listado y la disponibilidad.
"""

import uuid
from datetime import datetime, timezone, date, time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import DBSession, AdminUser, AnyStaff
from app.models.trabajador import Trabajador, EstadoTrabajador
from app.models.turno import Turno, EstadoTurno
from app.models.servicio import Servicio
from app.schemas.trabajador import (
    TrabajadorCreate, TrabajadorUpdate, TrabajadorResponse
)

router = APIRouter(
    prefix="/api/v1/trabajadores",
    tags=["trabajadores"],
)


# ─── Helper ───────────────────────────────────────────────────────────────────

def get_trabajador_o_404(
    trabajador_id: uuid.UUID,
    empresa_id: uuid.UUID,
    db: Session
) -> Trabajador:
    """Busca trabajador filtrando por empresa. Lanza 404 si no existe."""
    t = db.query(Trabajador).filter(
        Trabajador.id == trabajador_id,
        Trabajador.empresa_id == empresa_id,
    ).first()
    if not t:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trabajador {trabajador_id} no encontrado"
        )
    return t


def calcular_horarios_libres(
    trabajador: Trabajador,
    fecha: date,
    duracion_minutos: int,
    db: Session,
) -> list[dict]:
    """
    Calcula los bloques de tiempo disponibles de un trabajador en una fecha.

    Algoritmo:
    1. Obtiene el horario del día de la semana del trabajador
    2. Genera bloques cada N minutos (duracion del servicio)
    3. Descarta los bloques que solapan con turnos ya confirmados
    4. Descarta los bloques en días bloqueados
    5. Retorna los bloques libres

    Esto garantiza que no se puedan reservar 2 turnos al mismo tiempo.
    """
    DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    nombre_dia = DIAS[fecha.weekday()]

    horarios = trabajador.horarios or {}
    config_dia = horarios.get(nombre_dia, {})

    # Si el trabajador no trabaja ese día
    if not config_dia.get("activo", False):
        return []

    # Si el día está bloqueado (vacaciones, feriado)
    dias_bloqueados = trabajador.dias_bloqueados or []
    if str(fecha) in dias_bloqueados:
        return []

    # Turnos ya confirmados ese día para este trabajador
    turnos_ocupados = db.query(Turno).filter(
        Turno.trabajador_id == trabajador.id,
        Turno.fecha == fecha,
        Turno.estado.in_([
            EstadoTurno.CONFIRMADO,
            EstadoTurno.PENDIENTE,
            EstadoTurno.EN_CURSO,
        ])
    ).all()

    # Convertimos los turnos ocupados a rangos de tiempo
    ocupados = [(t.hora_inicio, t.hora_fin) for t in turnos_ocupados]

    # Generamos bloques de tiempo cada N minutos
    inicio_str = config_dia.get("inicio", "09:00")
    fin_str    = config_dia.get("fin",    "18:00")

    h_ini, m_ini = map(int, inicio_str.split(":"))
    h_fin, m_fin = map(int, fin_str.split(":"))

    inicio_minutos = h_ini * 60 + m_ini
    fin_minutos    = h_fin * 60 + m_fin

    bloques_libres = []
    cursor = inicio_minutos

    while cursor + duracion_minutos <= fin_minutos:
        bloque_ini = time(cursor // 60, cursor % 60)
        bloque_fin = time((cursor + duracion_minutos) // 60,
                          (cursor + duracion_minutos) % 60)

        # Verificamos si el bloque solapa con algún turno ocupado
        libre = True
        for ocup_ini, ocup_fin in ocupados:
            if bloque_ini < ocup_fin and bloque_fin > ocup_ini:
                libre = False
                break

        if libre:
            bloques_libres.append({
                "hora_inicio": bloque_ini.strftime("%H:%M"),
                "hora_fin":    bloque_fin.strftime("%H:%M"),
            })

        cursor += duracion_minutos

    return bloques_libres


# ─── POST /trabajadores — Crear ────────────────────────────────────────────────

@router.post(
    "/",
    response_model=TrabajadorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear trabajador",
)
def crear_trabajador(
    data: TrabajadorCreate,
    db: DBSession,
    current_user: AdminUser,
):
    """
    Crea un nuevo trabajador en la empresa.
    Solo el ADMIN puede crear trabajadores.

    Verifica el límite de trabajadores según el plan de la empresa
    antes de crear (FREE = 1, BASIC = 2, PRO = 10, ENTERPRISE = ilimitado).
    """
    from app.models.empresa import Empresa

    empresa = db.query(Empresa).filter(
        Empresa.id == current_user.empresa_id
    ).first()

    # Verificar límite del plan
    if empresa and empresa.max_trabajadores:
        activos = db.query(Trabajador).filter(
            Trabajador.empresa_id == current_user.empresa_id,
            Trabajador.estado == EstadoTrabajador.ACTIVO,
        ).count()

        if activos >= empresa.max_trabajadores:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error":   "limite_trabajadores",
                    "mensaje": f"Tu plan permite hasta {empresa.max_trabajadores} trabajadores activos. "
                               f"Actualizá tu plan para agregar más.",
                    "actual":  activos,
                    "limite":  empresa.max_trabajadores,
                }
            )

    trabajador = Trabajador(
        empresa_id=current_user.empresa_id,
        **data.model_dump(exclude_none=True)
    )
    db.add(trabajador)
    db.commit()
    db.refresh(trabajador)
    return trabajador


# ─── GET /trabajadores — Listar ────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[TrabajadorResponse],
    summary="Listar trabajadores",
)
def listar_trabajadores(
    db: DBSession,
    current_user: AnyStaff,
    solo_activos: bool = Query(True, description="Si True, solo devuelve trabajadores activos"),
):
    """
    Lista los trabajadores de la empresa ordenados por orden_display.
    Por defecto solo muestra los activos.
    """
    query = db.query(Trabajador).filter(
        Trabajador.empresa_id == current_user.empresa_id,
    )
    if solo_activos:
        query = query.filter(Trabajador.activo == True)

    return query.order_by(Trabajador.orden_display, Trabajador.nombre).all()


# ─── GET /trabajadores/{id} — Detalle ─────────────────────────────────────────

@router.get(
    "/{trabajador_id}",
    response_model=TrabajadorResponse,
    summary="Obtener trabajador",
)
def obtener_trabajador(
    trabajador_id: uuid.UUID,
    db: DBSession,
    current_user: AnyStaff,
):
    return get_trabajador_o_404(trabajador_id, current_user.empresa_id, db)


# ─── GET /trabajadores/{id}/disponibilidad — Horarios libres ──────────────────

@router.get(
    "/{trabajador_id}/disponibilidad",
    summary="Ver disponibilidad",
    description="Retorna los bloques de tiempo libre de un trabajador "
                "para una fecha y duración de servicio específicas."
)
def obtener_disponibilidad(
    trabajador_id: uuid.UUID,
    fecha: date = Query(..., description="Fecha a consultar (YYYY-MM-DD)"),
    duracion_minutos: int = Query(30, ge=5, le=480, description="Duración del servicio en minutos"),
    db: DBSession = None,
    current_user: AnyStaff = None,
):
    """
    Calcula los horarios disponibles de un trabajador en una fecha.

    Usa este endpoint para mostrar el selector de horario cuando
    un cliente quiere reservar un turno.

    Retorna una lista de bloques con hora_inicio y hora_fin
    que no se superponen con turnos ya confirmados.
    """
    if fecha < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede consultar disponibilidad para fechas pasadas"
        )

    trabajador = get_trabajador_o_404(trabajador_id, current_user.empresa_id, db)

    bloques = calcular_horarios_libres(
        trabajador, fecha, duracion_minutos, db
    )

    return {
        "trabajador_id":  str(trabajador_id),
        "trabajador":     f"{trabajador.nombre} {trabajador.apellido or ''}".strip(),
        "fecha":          str(fecha),
        "duracion_min":   duracion_minutos,
        "total_disponibles": len(bloques),
        "bloques":        bloques,
    }


# ─── PATCH /trabajadores/{id} — Actualizar ────────────────────────────────────

@router.patch(
    "/{trabajador_id}",
    response_model=TrabajadorResponse,
    summary="Actualizar trabajador",
)
def actualizar_trabajador(
    trabajador_id: uuid.UUID,
    data: TrabajadorUpdate,
    db: DBSession,
    current_user: AdminUser,
):
    """
    Actualiza campos del trabajador. Solo el ADMIN puede modificar trabajadores.
    Los campos no enviados no se modifican.
    """
    trabajador = get_trabajador_o_404(trabajador_id, current_user.empresa_id, db)

    campos = data.model_dump(exclude_none=True)
    if not campos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos para actualizar"
        )

    for campo, valor in campos.items():
        setattr(trabajador, campo, valor)

    trabajador.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(trabajador)
    return trabajador


# ─── DELETE /trabajadores/{id} — Soft delete ──────────────────────────────────

@router.delete(
    "/{trabajador_id}",
    summary="Desactivar trabajador",
)
def desactivar_trabajador(
    trabajador_id: uuid.UUID,
    db: DBSession,
    current_user: AdminUser,
):
    """
    Desactiva el trabajador (soft delete).
    Sus turnos pasados y calificaciones se conservan para el historial.
    Los turnos futuros quedan en estado PENDIENTE para reasignar.
    """
    trabajador = get_trabajador_o_404(trabajador_id, current_user.empresa_id, db)

    if not trabajador.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El trabajador ya está desactivado"
        )

    trabajador.activo = True
    trabajador.estado = EstadoTrabajador.INACTIVO
    trabajador.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "mensaje": f"Trabajador {trabajador.nombre} desactivado",
        "id": str(trabajador_id)
    }