"""
routers/turnos.py — El corazón del sistema de turnos.

Endpoints:
  POST   /api/v1/turnos                → reservar turno (con validaciones completas)
  GET    /api/v1/turnos                → listar turnos con filtros
  GET    /api/v1/turnos/{id}           → detalle del turno
  POST   /api/v1/turnos/{id}/confirmar → confirmar turno pendiente
  POST   /api/v1/turnos/{id}/cancelar  → cancelar turno
  POST   /api/v1/turnos/{id}/ausente   → marcar cliente ausente (no-show)
  POST   /api/v1/turnos/{id}/atender   → marcar turno como atendido
  PATCH  /api/v1/turnos/{id}/notas     → cargar notas post-atención
"""

import uuid
from datetime import datetime, timezone, date, time, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.dependencies import DBSession, AdminOrRecep, AnyStaff, AdminUser
from app.models.turno import Turno, EstadoTurno, OrigenTurno, CanceladoPor
from app.models.cliente import Cliente, EstadoCliente
from app.models.trabajador import Trabajador, EstadoTrabajador
from app.models.servicio import Servicio
from app.models.historial import HistorialCliente, TipoEvento
from app.schemas.turno import (
    TurnoCreate, TurnoCambioEstado,
    TurnoNotasUpdate, TurnoResponse, TurnoListItem
)

router = APIRouter(prefix="/api/v1/turnos", tags=["turnos"])


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_turno_o_404(turno_id: uuid.UUID, empresa_id: uuid.UUID, db: Session) -> Turno:
    t = db.query(Turno).filter(
        Turno.id == turno_id,
        Turno.empresa_id == empresa_id,
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail=f"Turno {turno_id} no encontrado")
    return t


def str_a_time(hora_str: str) -> time:
    """Convierte '09:30' a time(9, 30)."""
    h, m = map(int, hora_str.split(":"))
    return time(h, m)


def hay_solapamiento(
    db: Session,
    trabajador_id: uuid.UUID,
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
    excluir_turno_id: Optional[uuid.UUID] = None,
) -> bool:
    """
    Verifica si un bloque de tiempo solapa con turnos existentes.

    Un turno solapa si:
    - El nuevo inicio es anterior al fin de un turno existente
    - Y el nuevo fin es posterior al inicio de un turno existente

    Se excluyen los turnos cancelados, ausentes y reprogramados.
    """
    query = db.query(Turno).filter(
        Turno.trabajador_id == trabajador_id,
        Turno.fecha == fecha,
        Turno.estado.in_([
            EstadoTurno.PENDIENTE,
            EstadoTurno.CONFIRMADO,
            EstadoTurno.EN_CURSO,
        ]),
        Turno.hora_inicio < hora_fin,
        Turno.hora_fin > hora_inicio,
    )
    if excluir_turno_id:
        query = query.filter(Turno.id != excluir_turno_id)

    return query.first() is not None


def enriquecer_turno(turno: Turno, db: Session) -> dict:
    """
    Agrega nombres del cliente, trabajador y servicio al objeto turno
    para evitar N+1 queries en el frontend.
    """
    cliente    = db.get(Cliente,    turno.cliente_id)
    trabajador = db.get(Trabajador, turno.trabajador_id)
    servicio   = db.get(Servicio,   turno.servicio_id)

    data = {c.name: getattr(turno, c.name) for c in turno.__table__.columns}
    data["duracion_minutos"] = turno.duracion_minutos
    data["cliente_nombre"]    = f"{cliente.nombre} {cliente.apellido or ''}".strip() if cliente else None
    data["trabajador_nombre"] = f"{trabajador.nombre} {trabajador.apellido or ''}".strip() if trabajador else None
    data["servicio_nombre"]   = servicio.nombre if servicio else None
    return data


def registrar_evento_historial(
    db: Session,
    cliente_id: uuid.UUID,
    empresa_id: uuid.UUID,
    tipo: TipoEvento,
    descripcion: str,
    turno_id: Optional[uuid.UUID] = None,
    creado_por_id: Optional[uuid.UUID] = None,
    datos_extra: Optional[dict] = None,
):
    """
    Registra un evento en el historial cronológico del cliente.
    Se llama en cada acción importante sobre un turno.
    """
    evento = HistorialCliente(
        cliente_id=cliente_id,
        empresa_id=empresa_id,
        tipo_evento=tipo,
        descripcion=descripcion,
        turno_id=turno_id,
        creado_por_id=creado_por_id,
        datos_extra=datos_extra or {},
    )
    db.add(evento)


# ─── POST /turnos — Crear turno ───────────────────────────────────────────────

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Reservar turno",
)
def crear_turno(data: TurnoCreate, db: DBSession, current_user: AdminOrRecep):
    """
    Reserva un turno aplicando todas las validaciones de negocio:

    1. Cliente existe y está activo en la empresa
    2. Trabajador existe, está activo y trabaja ese día
    3. El servicio existe y el trabajador puede realizarlo
    4. El horario no solapa con otro turno confirmado
    5. El horario está dentro del horario laboral del trabajador
    6. Calcula hora_fin automáticamente
    7. Copia el precio del servicio al momento de la reserva
    8. Registra el evento en el historial del cliente
    """

    empresa_id = current_user.empresa_id

    # ── 1. Validar cliente ────────────────────────────────────────────────────
    cliente = db.query(Cliente).filter(
        Cliente.id == data.cliente_id,
        Cliente.empresa_id == empresa_id,
    ).first()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if cliente.estado == EstadoCliente.BLOQUEADO:
        raise HTTPException(status_code=400, detail="El cliente está bloqueado y no puede reservar turnos")

    # ── 2. Validar trabajador ─────────────────────────────────────────────────
    trabajador = db.query(Trabajador).filter(
        Trabajador.id == data.trabajador_id,
        Trabajador.empresa_id == empresa_id,
        Trabajador.activo == True,
    ).first()

    if not trabajador:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado o inactivo")

    # ── 3. Validar servicio ───────────────────────────────────────────────────
    servicio = db.query(Servicio).filter(
        Servicio.id == data.servicio_id,
        Servicio.empresa_id == empresa_id,
        Servicio.activo == True,
    ).first()

    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado o inactivo")

    # ── 4. Validar horario del trabajador ─────────────────────────────────────
    DIAS = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]
    nombre_dia = DIAS[data.fecha.weekday()]
    horarios = trabajador.horarios or {}
    config_dia = horarios.get(nombre_dia, {})

    if not config_dia.get("activo", False):
        raise HTTPException(
            status_code=400,
            detail=f"{trabajador.nombre} no trabaja los {nombre_dia}s"
        )

    # Verificar días bloqueados
    dias_bloqueados = trabajador.dias_bloqueados or []
    if str(data.fecha) in dias_bloqueados:
        raise HTTPException(
            status_code=400,
            detail=f"{trabajador.nombre} tiene ese día bloqueado"
        )

    # ── 5. Calcular hora_fin ──────────────────────────────────────────────────
    hora_inicio = str_a_time(data.hora_inicio)
    inicio_dt   = datetime.combine(data.fecha, hora_inicio)
    fin_dt      = inicio_dt + timedelta(minutes=servicio.duracion_minutos)
    hora_fin    = fin_dt.time()

    # Verificar que el turno cierra antes del fin de la jornada
    fin_jornada = str_a_time(config_dia.get("fin", "18:00"))
    if hora_fin > fin_jornada:
        raise HTTPException(
            status_code=400,
            detail=f"El turno termina a las {hora_fin.strftime('%H:%M')} "
                   f"pero {trabajador.nombre} termina a las {config_dia['fin']}"
        )

    # ── 6. Verificar solapamiento ─────────────────────────────────────────────
    if hay_solapamiento(db, data.trabajador_id, data.fecha, hora_inicio, hora_fin):
        raise HTTPException(
            status_code=409,
            detail=f"El horario {data.hora_inicio} ya está ocupado para {trabajador.nombre}"
        )

    # ── 7. Calcular precio final ──────────────────────────────────────────────
    precio_base  = servicio.precio_vigente
    descuento    = 0.0
    precio_final = precio_base

    if data.descuento_id:
        from app.models.descuento import Descuento
        descuento_obj = db.query(Descuento).filter(
            Descuento.id == data.descuento_id,
            Descuento.empresa_id == empresa_id,
        ).first()
        if descuento_obj and descuento_obj.esta_vigente:
            descuento    = descuento_obj.calcular_descuento(precio_base)
            precio_final = precio_base - descuento
            descuento_obj.usos_actuales = (descuento_obj.usos_actuales or 0) + 1

    # ── 8. Crear el turno ─────────────────────────────────────────────────────
    turno = Turno(
        empresa_id    = empresa_id,
        cliente_id    = data.cliente_id,
        trabajador_id = data.trabajador_id,
        servicio_id   = data.servicio_id,
        fecha         = data.fecha,
        hora_inicio   = hora_inicio,
        hora_fin      = hora_fin,
        estado        = EstadoTurno.PENDIENTE,
        origen        = data.origen,
        notas_cliente = data.notas_cliente,
        precio_base      = precio_base,
        descuento_monto  = descuento,
        precio_final     = precio_final,
        descuento_id     = data.descuento_id,
        suscripcion_id   = data.suscripcion_id,
        cubierto_por_plan= data.suscripcion_id is not None,
    )
    db.add(turno)

    # ── 9. Registrar en historial del cliente ─────────────────────────────────
    registrar_evento_historial(
        db=db,
        cliente_id=data.cliente_id,
        empresa_id=empresa_id,
        tipo=TipoEvento.VISITA,
        descripcion=f"Turno reservado: {servicio.nombre} con {trabajador.nombre} "
                    f"el {data.fecha.strftime('%d/%m/%Y')} a las {data.hora_inicio}",
        turno_id=turno.id,
        creado_por_id=current_user.id,
        datos_extra={
            "servicio":  servicio.nombre,
            "trabajador": trabajador.nombre,
            "precio":    precio_final,
            "origen":    data.origen.value,
        },
    )

    db.commit()
    db.refresh(turno)
    return enriquecer_turno(turno, db)


# ─── GET /turnos — Listar ─────────────────────────────────────────────────────

@router.get("/", summary="Listar turnos")
def listar_turnos(
    db: DBSession,
    current_user: AnyStaff,
    fecha:         Optional[date]        = Query(None),
    fecha_desde:   Optional[date]        = Query(None),
    fecha_hasta:   Optional[date]        = Query(None),
    estado:        Optional[EstadoTurno] = Query(None),
    trabajador_id: Optional[uuid.UUID]   = Query(None),
    cliente_id:    Optional[uuid.UUID]   = Query(None),
    pagina:        int = Query(1, ge=1),
    por_pagina:    int = Query(50, ge=1, le=200),
):
    """
    Lista turnos con múltiples filtros.
    El trabajador solo ve sus propios turnos.
    Admin y recepcionista ven todos.
    """
    from app.models.usuario import RolUsuario

    query = db.query(Turno).filter(Turno.empresa_id == current_user.empresa_id)

    # Los trabajadores solo ven sus propios turnos
    if current_user.rol == RolUsuario.TRABAJADOR:
        trab = db.query(Trabajador).filter(
            Trabajador.usuario_id == current_user.id
        ).first()
        if trab:
            query = query.filter(Turno.trabajador_id == trab.id)

    if fecha:
        query = query.filter(Turno.fecha == fecha)
    if fecha_desde:
        query = query.filter(Turno.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Turno.fecha <= fecha_hasta)
    if estado:
        query = query.filter(Turno.estado == estado)
    if trabajador_id:
        query = query.filter(Turno.trabajador_id == trabajador_id)
    if cliente_id:
        query = query.filter(Turno.cliente_id == cliente_id)

    total  = query.count()
    turnos = query.order_by(Turno.fecha, Turno.hora_inicio)\
                  .offset((pagina - 1) * por_pagina)\
                  .limit(por_pagina).all()

    return {
        "items":      [enriquecer_turno(t, db) for t in turnos],
        "total":      total,
        "pagina":     pagina,
        "por_pagina": por_pagina,
    }


# ─── GET /turnos/{id} — Detalle ───────────────────────────────────────────────

@router.get("/{turno_id}", summary="Obtener turno")
def obtener_turno(turno_id: uuid.UUID, db: DBSession, current_user: AnyStaff):
    turno = get_turno_o_404(turno_id, current_user.empresa_id, db)
    return enriquecer_turno(turno, db)


# ─── POST /turnos/{id}/confirmar ──────────────────────────────────────────────

@router.post("/{turno_id}/confirmar", summary="Confirmar turno")
def confirmar_turno(turno_id: uuid.UUID, db: DBSession, current_user: AdminOrRecep):
    """Confirma un turno pendiente. Dispara el envío de confirmación por WhatsApp."""
    turno = get_turno_o_404(turno_id, current_user.empresa_id, db)

    if turno.estado != EstadoTurno.PENDIENTE:
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden confirmar turnos pendientes. Estado actual: {turno.estado}"
        )

    turno.estado     = EstadoTurno.CONFIRMADO
    turno.updated_at = datetime.now(timezone.utc)

    registrar_evento_historial(
        db=db,
        cliente_id=turno.cliente_id,
        empresa_id=turno.empresa_id,
        tipo=TipoEvento.CONTACTO,
        descripcion="Turno confirmado",
        turno_id=turno.id,
        creado_por_id=current_user.id,
    )

    db.commit()
    db.refresh(turno)
    return enriquecer_turno(turno, db)


# ─── POST /turnos/{id}/cancelar ───────────────────────────────────────────────

@router.post("/{turno_id}/cancelar", summary="Cancelar turno")
def cancelar_turno(
    turno_id: uuid.UUID,
    motivo:   Optional[str]          = Query(None),
    por:      CanceladoPor           = Query(CanceladoPor.NEGOCIO),
    db: DBSession = None,
    current_user: AdminOrRecep = None,
):
    """
    Cancela un turno. Registra quién canceló y el motivo.
    No se pueden cancelar turnos ya atendidos o ausentes.
    """
    turno = get_turno_o_404(turno_id, current_user.empresa_id, db)

    estados_finales = [EstadoTurno.ATENDIDO, EstadoTurno.AUSENTE, EstadoTurno.CANCELADO]
    if turno.estado in estados_finales:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede cancelar un turno en estado: {turno.estado}"
        )

    turno.estado              = EstadoTurno.CANCELADO
    turno.motivo_cancelacion  = motivo
    turno.cancelado_por       = por
    turno.cancelado_at        = datetime.now(timezone.utc)
    turno.updated_at          = datetime.now(timezone.utc)

    registrar_evento_historial(
        db=db,
        cliente_id=turno.cliente_id,
        empresa_id=turno.empresa_id,
        tipo=TipoEvento.CONTACTO,
        descripcion=f"Turno cancelado por {por.value}. {f'Motivo: {motivo}' if motivo else ''}",
        turno_id=turno.id,
        creado_por_id=current_user.id,
    )

    db.commit()
    return {"mensaje": "Turno cancelado", "id": str(turno_id)}


# ─── POST /turnos/{id}/ausente ────────────────────────────────────────────────

@router.post("/{turno_id}/ausente", summary="Marcar como ausente (no-show)")
def marcar_ausente(turno_id: uuid.UUID, db: DBSession, current_user: AdminOrRecep):
    """
    Marca al cliente como ausente (no vino sin avisar).
    Incrementa el contador de ausencias del cliente.
    Este dato se usa para detectar clientes no confiables.
    """
    turno = get_turno_o_404(turno_id, current_user.empresa_id, db)

    if turno.estado not in [EstadoTurno.PENDIENTE, EstadoTurno.CONFIRMADO]:
        raise HTTPException(status_code=400, detail="El turno no está en estado válido para ausencia")

    turno.estado     = EstadoTurno.AUSENTE
    turno.updated_at = datetime.now(timezone.utc)

    # Incrementamos el contador de ausencias del cliente
    cliente = db.get(Cliente, turno.cliente_id)
    if cliente:
        cliente.ausencias = (cliente.ausencias or 0) + 1

    # Incrementamos el contador del trabajador
    trabajador = db.get(Trabajador, turno.trabajador_id)
    if trabajador:
        trabajador.total_ausencias = (trabajador.total_ausencias or 0) + 1

    registrar_evento_historial(
        db=db,
        cliente_id=turno.cliente_id,
        empresa_id=turno.empresa_id,
        tipo=TipoEvento.AUSENCIA,
        descripcion="Cliente no se presentó al turno sin avisar",
        turno_id=turno.id,
        creado_por_id=current_user.id,
    )

    db.commit()
    return {"mensaje": "Turno marcado como ausente", "ausencias_cliente": cliente.ausencias if cliente else 0}


# ─── POST /turnos/{id}/atender ────────────────────────────────────────────────

@router.post("/{turno_id}/atender", summary="Marcar turno como atendido")
def marcar_atendido(turno_id: uuid.UUID, db: DBSession, current_user: AnyStaff):
    """
    Marca el turno como atendido y actualiza estadísticas del cliente y trabajador:
    - Incrementa total_visitas del cliente
    - Actualiza ultima_visita del cliente
    - Suma el precio al total_gastado del cliente
    - Incrementa total_atenciones del trabajador
    - Recalcula ticket_promedio del trabajador
    - Actualiza nivel de fidelización si corresponde
    """
    turno = get_turno_o_404(turno_id, current_user.empresa_id, db)

    if turno.estado not in [EstadoTurno.CONFIRMADO, EstadoTurno.EN_CURSO, EstadoTurno.PENDIENTE]:
        raise HTTPException(status_code=400, detail="El turno no está en estado válido para marcar como atendido")

    turno.estado          = EstadoTurno.ATENDIDO
    turno.hora_fin_real   = datetime.now(timezone.utc)
    turno.updated_at      = datetime.now(timezone.utc)

    # ── Actualizar estadísticas del cliente ───────────────────────────────────
    cliente = db.get(Cliente, turno.cliente_id)
    if cliente:
        cliente.total_visitas  = (cliente.total_visitas or 0) + 1
        cliente.ultima_visita  = datetime.now(timezone.utc)
        cliente.total_gastado  = (cliente.total_gastado or 0.0) + (turno.precio_final or 0.0)

        if not cliente.primera_visita:
            cliente.primera_visita = datetime.now(timezone.utc)

        # Recalcular nivel de fidelización
        visitas = cliente.total_visitas
        from app.models.cliente import NivelFidelizacion
        if visitas >= 25:
            cliente.nivel_fidelizacion = NivelFidelizacion.VIP
        elif visitas >= 10:
            cliente.nivel_fidelizacion = NivelFidelizacion.FRECUENTE
        elif visitas >= 3:
            cliente.nivel_fidelizacion = NivelFidelizacion.REGULAR

    # ── Actualizar estadísticas del trabajador ────────────────────────────────
    trabajador = db.get(Trabajador, turno.trabajador_id)
    if trabajador:
        trabajador.total_atenciones = (trabajador.total_atenciones or 0) + 1
        # Recalcular ticket promedio
        if trabajador.total_atenciones > 0 and turno.precio_final:
            total_acum = (trabajador.ticket_promedio or 0) * (trabajador.total_atenciones - 1)
            trabajador.ticket_promedio = (total_acum + turno.precio_final) / trabajador.total_atenciones

    registrar_evento_historial(
        db=db,
        cliente_id=turno.cliente_id,
        empresa_id=turno.empresa_id,
        tipo=TipoEvento.VISITA,
        descripcion=f"Atendido: {db.get(Servicio, turno.servicio_id).nombre if db.get(Servicio, turno.servicio_id) else 'Servicio'} "
                    f"— Total: ${turno.precio_final or 0:.0f}",
        turno_id=turno.id,
        creado_por_id=current_user.id,
        datos_extra={"precio_final": turno.precio_final, "visita_numero": cliente.total_visitas if cliente else 0},
    )

    db.commit()
    return enriquecer_turno(turno, db)


# ─── PATCH /turnos/{id}/notas ─────────────────────────────────────────────────

@router.patch("/{turno_id}/notas", summary="Cargar notas post-atención")
def cargar_notas(
    turno_id: uuid.UUID,
    data: TurnoNotasUpdate,
    db: DBSession,
    current_user: AnyStaff,
):
    """
    El trabajador carga sus observaciones después de atender.
    También se actualiza notas_ultimo_servicio en el perfil del cliente.
    Ej: 'Usé la tijera número 4, le quedó muy bien el degradado.'
    """
    turno = get_turno_o_404(turno_id, current_user.empresa_id, db)

    turno.notas_post_servicio = data.notas_post_servicio
    turno.updated_at          = datetime.now(timezone.utc)

    # Propagamos la nota al perfil del cliente para acceso rápido
    cliente = db.get(Cliente, turno.cliente_id)
    if cliente:
        cliente.notas_ultimo_servicio = data.notas_post_servicio

    db.commit()
    return {"mensaje": "Notas guardadas", "turno_id": str(turno_id)}