"""
routers/pagos.py — Módulo financiero completo.

Endpoints:
  POST  /api/v1/pagos                      → registrar pago de un turno
  GET   /api/v1/pagos                      → historial de ventas con filtros
  GET   /api/v1/pagos/cierre-caja          → resumen financiero del día
  GET   /api/v1/pagos/resumen-periodo      → resumen por rango de fechas
  PUT   /api/v1/pagos/comisiones           → configurar % por método
  GET   /api/v1/pagos/comisiones           → ver % actuales
"""

import uuid
from datetime import date, datetime, timezone
from typing import Optional, List
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.dependencies import DBSession, AdminUser, AdminOrRecep, AnyStaff
from app.models.pago import Pago, MetodoPago, EstadoPago
from app.models.turno import Turno, EstadoTurno
from app.models.cliente import Cliente
from app.models.trabajador import Trabajador
from app.models.servicio import Servicio
from app.models.empresa import Empresa
from app.schemas.pago import (
    PagoCreate, PagoResponse,
    CierreCaja, ResumenMetodo,
    ConfigComisionesUpdate
)

router = APIRouter(prefix="/api/v1/pagos", tags=["finanzas"])


# ─── Helper: obtener comisiones configuradas ──────────────────────────────────

def get_comisiones(empresa: Empresa) -> dict:
    """
    Retorna el mapa de comisiones de la empresa.
    Si no están configuradas, usa los defaults seguros (todo en 0%).
    """
    config = empresa.configuracion or {}
    return config.get("comisiones", {
        "efectivo":      0.0,
        "debito":        0.0,
        "credito":       0.0,
        "mercadopago":   0.0,
        "transferencia": 0.0,
        "gift_card":     0.0,
        "suscripcion":   0.0,
    })


def calcular_neto(monto: float, metodo: MetodoPago, comisiones: dict) -> tuple:
    """
    Calcula comisión y monto neto para un pago.
    Retorna (porcentaje, monto_comision, monto_neto).
    """
    porcentaje = comisiones.get(metodo.value, 0.0)
    monto_com  = round(monto * porcentaje / 100, 2)
    monto_neto = round(monto - monto_com, 2)
    return porcentaje, monto_com, monto_neto


def enriquecer_pago(pago: Pago, db: Session) -> dict:
    """Agrega nombres de cliente, trabajador y servicio al pago."""
    data = {c.name: getattr(pago, c.name) for c in pago.__table__.columns}

    if pago.cliente_id:
        c = db.get(Cliente, pago.cliente_id)
        data["cliente_nombre"] = f"{c.nombre} {c.apellido or ''}".strip() if c else None

    if pago.trabajador_id:
        t = db.get(Trabajador, pago.trabajador_id)
        data["trabajador_nombre"] = f"{t.nombre} {t.apellido or ''}".strip() if t else None

    if pago.turno_id:
        turno = db.get(Turno, pago.turno_id)
        if turno and turno.servicio_id:
            s = db.get(Servicio, turno.servicio_id)
            data["servicio_nombre"] = s.nombre if s else None

    return data


# ─── GET /pagos/comisiones — Ver comisiones actuales ──────────────────────────

@router.get(
    "/comisiones",
    summary="Ver comisiones configuradas",
    description="Muestra el porcentaje de comisión configurado por cada método de pago."
)
def get_comisiones_config(db: DBSession, current_user: AdminUser):
    empresa = db.get(Empresa, current_user.empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    comisiones = get_comisiones(empresa)

    return {
        "comisiones": comisiones,
        "descripcion": {
            "efectivo":      "Sin comisión — el dinero es 100% tuyo",
            "debito":        f"{comisiones.get('debito', 0)}% — posnet débito",
            "credito":       f"{comisiones.get('credito', 0)}% — posnet crédito (el más caro)",
            "mercadopago":   f"{comisiones.get('mercadopago', 0)}% — QR o link de pago",
            "transferencia": f"{comisiones.get('transferencia', 0)}% — transferencia bancaria",
        }
    }


# ─── PUT /pagos/comisiones — Configurar comisiones ────────────────────────────

@router.put(
    "/comisiones",
    summary="Configurar comisiones por método de pago",
    description="El admin define el porcentaje que cobra cada método. "
                "Se aplica a todos los futuros pagos."
)
def actualizar_comisiones(
    data: ConfigComisionesUpdate,
    db: DBSession,
    current_user: AdminUser,
):
    """
    Actualiza la configuración de comisiones de la empresa.

    Los porcentajes son:
    - Efectivo: 0% (sin costo)
    - Débito: ~1.5% (posnet)
    - Crédito: ~9% (posnet cuotas o sin cuotas)
    - MercadoPago: ~5.99% (QR o link)
    - Transferencia: 0% (sin costo)

    IMPORTANTE: el historial de pagos mantiene el % vigente al
    momento del cobro. Cambiar la comisión no afecta pagos pasados.
    """
    empresa = db.get(Empresa, current_user.empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    config = empresa.configuracion or {}
    config["comisiones"] = {
        "efectivo":      data.efectivo,
        "debito":        data.debito,
        "credito":       data.credito,
        "mercadopago":   data.mercadopago,
        "transferencia": data.transferencia,
        "gift_card":     0.0,
        "suscripcion":   0.0,
    }
    empresa.configuracion = config
    db.commit()

    return {
        "mensaje": "Comisiones actualizadas correctamente",
        "comisiones": config["comisiones"]
    }


# ─── POST /pagos — Registrar pago ─────────────────────────────────────────────

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar pago",
    description="Registra el pago de un turno. "
                "Calcula automáticamente la comisión y el monto neto."
)
def registrar_pago(
    data: PagoCreate,
    db: DBSession,
    current_user: AdminOrRecep,
):
    """
    Registra el cobro de un turno con el método de pago utilizado.

    El sistema:
    1. Busca el turno y verifica que pertenece a la empresa
    2. Obtiene la comisión configurada para ese método
    3. Calcula monto neto = bruto - comisión
    4. Guarda el pago con toda la info para el historial
    5. Marca el turno como pagado

    Si el turno ya tiene un pago registrado, lanza error
    para evitar cobros dobles.
    """
    empresa_id = current_user.empresa_id

    # Verificar el turno
    turno = db.query(Turno).filter(
        Turno.id == data.turno_id,
        Turno.empresa_id == empresa_id,
    ).first()

    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    if turno.estado not in [EstadoTurno.ATENDIDO, EstadoTurno.CONFIRMADO]:
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden registrar pagos de turnos atendidos o confirmados. "
                   f"Estado actual: {turno.estado}"
        )

    # Verificar que no tenga pago previo
    pago_existente = db.query(Pago).filter(
        Pago.turno_id == data.turno_id,
        Pago.estado == EstadoPago.PAGADO,
    ).first()

    if pago_existente:
        raise HTTPException(
            status_code=409,
            detail="Este turno ya tiene un pago registrado"
        )

    # Calcular comisión
    empresa    = db.get(Empresa, empresa_id)
    comisiones = get_comisiones(empresa)
    porcentaje, monto_com, monto_neto = calcular_neto(
        data.monto, data.metodo, comisiones
    )

    # Crear el pago
    pago = Pago(
        empresa_id           = empresa_id,
        turno_id             = data.turno_id,
        cliente_id           = turno.cliente_id,
        trabajador_id        = turno.trabajador_id,
        metodo               = data.metodo,
        monto                = data.monto,        # ← agregar
        monto_final          = monto_neto,        # ← agregar
        monto_bruto          = data.monto,
        comision_porcentaje  = porcentaje,
        comision_monto       = monto_com,
        monto_neto           = monto_neto,
        facturado            = data.facturado,
        notas                = data.notas,
        estado               = EstadoPago.PAGADO,
    )
    db.add(pago)

    # Actualizamos el turno
    turno.precio_final = data.monto
    turno.estado       = EstadoTurno.ATENDIDO
    turno.updated_at   = datetime.now(timezone.utc)

    db.commit()
    db.refresh(pago)

    return enriquecer_pago(pago, db)


# ─── GET /pagos — Historial de ventas ─────────────────────────────────────────

@router.get(
    "/",
    summary="Historial de ventas",
    description="Lista todos los pagos con filtros por fecha, método y facturación."
)
def historial_pagos(
    db: DBSession,
    current_user: AdminUser,
    fecha_desde:   Optional[date]       = Query(None),
    fecha_hasta:   Optional[date]       = Query(None),
    metodo:        Optional[MetodoPago] = Query(None),
    facturado:     Optional[bool]       = Query(None),
    trabajador_id: Optional[uuid.UUID]  = Query(None),
    pagina:        int = Query(1, ge=1),
    por_pagina:    int = Query(50, ge=1, le=200),
):
    """
    Historial completo de ventas con filtros.
    Incluye monto bruto, comisión y neto en cada registro.
    Exportable a CSV para el contador.
    """
    query = db.query(Pago).filter(
        Pago.empresa_id == current_user.empresa_id,
        Pago.estado == EstadoPago.PAGADO,
    )

    if fecha_desde:
        query = query.filter(func.date(Pago.created_at) >= fecha_desde)
    if fecha_hasta:
        query = query.filter(func.date(Pago.created_at) <= fecha_hasta)
    if metodo:
        query = query.filter(Pago.metodo == metodo)
    if facturado is not None:
        query = query.filter(Pago.facturado == facturado)
    if trabajador_id:
        query = query.filter(Pago.trabajador_id == trabajador_id)

    total  = query.count()
    pagos  = query.order_by(Pago.created_at.desc())\
                  .offset((pagina - 1) * por_pagina)\
                  .limit(por_pagina).all()

    # Totales del resultado filtrado
    totales = query.with_entities(
        func.sum(Pago.monto_bruto).label("bruto"),
        func.sum(Pago.comision_monto).label("comision"),
        func.sum(Pago.monto_neto).label("neto"),
    ).first()

    return {
        "items":         [enriquecer_pago(p, db) for p in pagos],
        "total_pagos":   total,
        "pagina":        pagina,
        "por_pagina":    por_pagina,
        "totales": {
            "bruto":    round(totales.bruto or 0, 2),
            "comision": round(totales.comision or 0, 2),
            "neto":     round(totales.neto or 0, 2),
        }
    }


# ─── GET /pagos/cierre-caja — Cierre del día ─────────────────────────────────

@router.get(
    "/cierre-caja",
    response_model=CierreCaja,
    summary="Cierre de caja",
    description="Resumen financiero completo de un día. "
                "Muestra bruto, comisiones y neto por método de pago."
)
def cierre_caja(
    db: DBSession,
    current_user: AdminUser,
    fecha: date = Query(default=None, description="Fecha del cierre (default: hoy)"),
):
    """
    El cierre de caja que el negocio hace al final del día.

    Muestra:
    - Cuántos turnos hubo (atendidos, ausentes, cancelados)
    - Cuánto cobró en bruto por cada método
    - Cuánto pagó de comisiones
    - Cuánto le quedó neto en el bolsillo
    - Cuánto facturó vs cuánto no facturó
    - El trabajador y servicio que más facturó
    - El horario pico del día
    """
    if not fecha:
        fecha = date.today()

    empresa_id = current_user.empresa_id

    # Turnos del día
    turnos_dia = db.query(Turno).filter(
        Turno.empresa_id == empresa_id,
        Turno.fecha == fecha,
    ).all()

    atendidos  = sum(1 for t in turnos_dia if t.estado == EstadoTurno.ATENDIDO)
    ausentes   = sum(1 for t in turnos_dia if t.estado == EstadoTurno.AUSENTE)
    cancelados = sum(1 for t in turnos_dia if t.estado == EstadoTurno.CANCELADO)

    # Pagos del día
    pagos_dia = db.query(Pago).filter(
        Pago.empresa_id == empresa_id,
        Pago.estado == EstadoPago.PAGADO,
        func.date(Pago.created_at) == fecha,
    ).all()

    # Agrupar por método
    por_metodo: dict = defaultdict(lambda: {
        "cantidad": 0, "bruto": 0.0, "comision_pct": 0.0,
        "comision": 0.0, "neto": 0.0
    })

    for pago in pagos_dia:
        m = pago.metodo.value
        por_metodo[m]["cantidad"]     += 1
        por_metodo[m]["bruto"]        += pago.monto_bruto
        por_metodo[m]["comision_pct"]  = pago.comision_porcentaje
        por_metodo[m]["comision"]     += pago.comision_monto
        por_metodo[m]["neto"]         += pago.monto_neto

    resumen_metodos = [
        ResumenMetodo(
            metodo=MetodoPago(m),
            cantidad_pagos=v["cantidad"],
            monto_bruto=round(v["bruto"], 2),
            comision_porcentaje=v["comision_pct"],
            comision_monto=round(v["comision"], 2),
            monto_neto=round(v["neto"], 2),
        )
        for m, v in por_metodo.items()
    ]

    total_bruto    = sum(p.monto_bruto     for p in pagos_dia)
    total_comision = sum(p.comision_monto  for p in pagos_dia)
    total_neto     = sum(p.monto_neto      for p in pagos_dia)
    facturado      = sum(p.monto_bruto     for p in pagos_dia if p.facturado)
    no_facturado   = sum(p.monto_bruto     for p in pagos_dia if not p.facturado)

    # Ticket promedio
    ticket_prom = round(total_bruto / len(pagos_dia), 2) if pagos_dia else 0.0

    # Trabajador top del día
    trabajador_top = None
    if pagos_dia:
        trab_facturacion: dict = defaultdict(float)
        for p in pagos_dia:
            if p.trabajador_id:
                trab_facturacion[p.trabajador_id] += p.monto_bruto
        if trab_facturacion:
            top_id = max(trab_facturacion, key=lambda x: trab_facturacion[x])
            t = db.get(Trabajador, top_id)
            if t:
                trabajador_top = f"{t.nombre} {t.apellido or ''}".strip()

    # Hora pico del día
    hora_pico = None
    if turnos_dia:
        hora_count: dict = defaultdict(int)
        for t in turnos_dia:
            if t.estado == EstadoTurno.ATENDIDO and t.hora_inicio:
                hora_str = t.hora_inicio.strftime("%H:00")
                hora_count[hora_str] += 1
        if hora_count:
            hora_pico = max(hora_count, key=lambda x: hora_count[x])

    # Servicio top del día
    servicio_top = None
    if turnos_dia:
        serv_count: dict = defaultdict(int)
        for t in turnos_dia:
            if t.estado == EstadoTurno.ATENDIDO and t.servicio_id:
                serv_count[t.servicio_id] += 1
        if serv_count:
            top_serv_id = max(serv_count, key=lambda x: serv_count[x])
            s = db.get(Servicio, top_serv_id)
            servicio_top = s.nombre if s else None

    return CierreCaja(
        fecha=fecha,
        empresa_id=empresa_id,
        total_turnos=len(turnos_dia),
        turnos_atendidos=atendidos,
        turnos_ausentes=ausentes,
        turnos_cancelados=cancelados,
        monto_bruto_total=round(total_bruto, 2),
        comision_total=round(total_comision, 2),
        monto_neto_total=round(total_neto, 2),
        facturado_monto=round(facturado, 2),
        no_facturado_monto=round(no_facturado, 2),
        por_metodo=resumen_metodos,
        hora_pico=hora_pico,
        trabajador_top=trabajador_top,
        servicio_top=servicio_top,
        ticket_promedio=ticket_prom,
    )


# ─── GET /pagos/resumen-periodo ───────────────────────────────────────────────

@router.get(
    "/resumen-periodo",
    summary="Resumen por período",
    description="Comparativa de facturación en un rango de fechas "
                "con totales diarios para graficar la evolución."
)
def resumen_periodo(
    db: DBSession,
    current_user: AdminUser,
    fecha_desde: date = Query(...),
    fecha_hasta: date = Query(...),
):
    """
    Devuelve la facturación día a día en el rango solicitado.
    Ideal para el gráfico de línea semanal/mensual del dashboard.
    """
    pagos = db.query(
        func.date(Pago.created_at).label("fecha"),
        func.sum(Pago.monto_bruto).label("bruto"),
        func.sum(Pago.comision_monto).label("comision"),
        func.sum(Pago.monto_neto).label("neto"),
        func.count(Pago.id).label("cantidad"),
    ).filter(
        Pago.empresa_id == current_user.empresa_id,
        Pago.estado == EstadoPago.PAGADO,
        func.date(Pago.created_at) >= fecha_desde,
        func.date(Pago.created_at) <= fecha_hasta,
    ).group_by(
        func.date(Pago.created_at)
    ).order_by(
        func.date(Pago.created_at)
    ).all()

    dias = [
        {
            "fecha":    str(p.fecha),
            "bruto":    round(p.bruto or 0, 2),
            "comision": round(p.comision or 0, 2),
            "neto":     round(p.neto or 0, 2),
            "cantidad": p.cantidad,
        }
        for p in pagos
    ]

    return {
        "fecha_desde":  str(fecha_desde),
        "fecha_hasta":  str(fecha_hasta),
        "dias":         dias,
        "totales": {
            "bruto":    round(sum(d["bruto"]    for d in dias), 2),
            "comision": round(sum(d["comision"] for d in dias), 2),
            "neto":     round(sum(d["neto"]     for d in dias), 2),
            "pagos":    sum(d["cantidad"]        for d in dias),
        }
    }