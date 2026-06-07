"""
routers/estadisticas.py — El cerebro analítico de TurnosPro.

Endpoints:
  GET /api/v1/estadisticas/resumen          → dashboard general
  GET /api/v1/estadisticas/heatmap          → ocupación por hora y día
  GET /api/v1/estadisticas/facturacion      → evolución de ingresos
  GET /api/v1/estadisticas/servicios        → ranking de servicios
  GET /api/v1/estadisticas/trabajadores     → performance del staff
  GET /api/v1/estadisticas/clientes         → análisis de clientes
  GET /api/v1/estadisticas/ausencias        → análisis de no-shows
  GET /api/v1/estadisticas/fidelizacion     → distribución por nivel
"""

from datetime import date, datetime, timezone, timedelta
from typing import Optional
from collections import defaultdict

from fastapi import APIRouter, Query
from sqlalchemy import func, extract, cast, Integer
from sqlalchemy.orm import Session

from app.dependencies import DBSession, AdminUser
from app.models.turno import Turno, EstadoTurno
from app.models.cliente import Cliente, NivelFidelizacion
from app.models.trabajador import Trabajador
from app.models.servicio import Servicio
from app.models.pago import Pago, EstadoPago
from app.models.historial import HistorialCliente

router = APIRouter(prefix="/api/v1/estadisticas", tags=["estadísticas"])


# ─── Helper: rango de fechas ──────────────────────────────────────────────────

def get_rango(periodo: str) -> tuple[date, date]:
    """
    Calcula fecha_desde y fecha_hasta según el período solicitado.
    Soporta: hoy, semana, mes, trimestre, año, y rango personalizado.
    """
    hoy = date.today()
    if periodo == "hoy":
        return hoy, hoy
    elif periodo == "semana":
        inicio = hoy - timedelta(days=hoy.weekday())
        return inicio, hoy
    elif periodo == "mes":
        return hoy.replace(day=1), hoy
    elif periodo == "trimestre":
        mes_inicio = ((hoy.month - 1) // 3) * 3 + 1
        return hoy.replace(month=mes_inicio, day=1), hoy
    elif periodo == "año":
        return hoy.replace(month=1, day=1), hoy
    else:
        return hoy.replace(day=1), hoy


def periodo_anterior(desde: date, hasta: date) -> tuple[date, date]:
    """Calcula el período anterior del mismo largo para comparación."""
    delta = hasta - desde
    return desde - delta - timedelta(days=1), desde - timedelta(days=1)


# ═══════════════════════════════════════════════════════════════════════════════
# RESUMEN GENERAL — el primer pantallazo al entrar al dashboard
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/resumen", summary="Resumen general del dashboard")
def resumen_general(
    db: DBSession,
    current_user: AdminUser,
    periodo: str = Query("mes", description="hoy | semana | mes | trimestre | año"),
):
    """
    El primer pantallazo al entrar al panel admin.
    Muestra los KPIs más importantes con comparación vs período anterior.

    Incluye: facturación, turnos, clientes nuevos, tasa de ausencias,
    ticket promedio, ocupación promedio y alertas importantes.
    """
    empresa_id = current_user.empresa_id
    desde, hasta = get_rango(periodo)
    desde_ant, hasta_ant = periodo_anterior(desde, hasta)

    # ── Turnos del período ────────────────────────────────────────────────────
    turnos = db.query(Turno).filter(
        Turno.empresa_id == empresa_id,
        Turno.fecha >= desde,
        Turno.fecha <= hasta,
    ).all()

    turnos_ant = db.query(Turno).filter(
        Turno.empresa_id == empresa_id,
        Turno.fecha >= desde_ant,
        Turno.fecha <= hasta_ant,
    ).all()

    total      = len(turnos)
    atendidos  = sum(1 for t in turnos if t.estado == EstadoTurno.ATENDIDO)
    ausentes   = sum(1 for t in turnos if t.estado == EstadoTurno.AUSENTE)
    cancelados = sum(1 for t in turnos if t.estado == EstadoTurno.CANCELADO)

    total_ant     = len(turnos_ant)
    atendidos_ant = sum(1 for t in turnos_ant if t.estado == EstadoTurno.ATENDIDO)

    tasa_ausencia    = round(ausentes / total * 100, 1) if total > 0 else 0.0
    tasa_cancelacion = round(cancelados / total * 100, 1) if total > 0 else 0.0

    # ── Facturación del período ───────────────────────────────────────────────
    pagos = db.query(Pago).filter(
        Pago.empresa_id == empresa_id,
        Pago.estado == EstadoPago.PAGADO,
        func.date(Pago.created_at) >= desde,
        func.date(Pago.created_at) <= hasta,
    ).all()

    pagos_ant = db.query(Pago).filter(
        Pago.empresa_id == empresa_id,
        Pago.estado == EstadoPago.PAGADO,
        func.date(Pago.created_at) >= desde_ant,
        func.date(Pago.created_at) <= hasta_ant,
    ).all()

    facturacion_bruta  = sum(p.monto_bruto for p in pagos)
    facturacion_neta   = sum(p.monto_neto for p in pagos)
    comisiones_pagadas = sum(p.comision_monto for p in pagos)
    facturacion_ant    = sum(p.monto_bruto for p in pagos_ant)
    ticket_prom        = facturacion_bruta / len(pagos) if pagos else 0.0

    # ── Variación vs período anterior ────────────────────────────────────────
    def variacion(actual, anterior):
        if anterior == 0:
            return 100.0 if actual > 0 else 0.0
        return round((actual - anterior) / anterior * 100, 1)

    # ── Clientes nuevos vs recurrentes ────────────────────────────────────────
    ids_clientes = {t.cliente_id for t in turnos if t.estado == EstadoTurno.ATENDIDO}
    clientes_nuevos = sum(
        1 for cid in ids_clientes
        if db.query(Turno).filter(
            Turno.cliente_id == cid,
            Turno.fecha < desde,
            Turno.estado == EstadoTurno.ATENDIDO,
        ).count() == 0
    )

    # ── Trabajador más productivo ─────────────────────────────────────────────
    trab_fact: dict = defaultdict(float)
    for p in pagos:
        if p.trabajador_id:
            trab_fact[p.trabajador_id] += p.monto_bruto

    trabajador_top = None
    if trab_fact:
        top_id = max(trab_fact, key=lambda x: trab_fact[x])
        t = db.get(Trabajador, top_id)
        if t:
            trabajador_top = {
                "nombre":      f"{t.nombre} {t.apellido or ''}".strip(),
                "facturacion": round(trab_fact[top_id], 2),
            }

    # ── Servicio más vendido ──────────────────────────────────────────────────
    serv_count: dict = defaultdict(int)
    for t in turnos:
        if t.estado == EstadoTurno.ATENDIDO and t.servicio_id:
            serv_count[t.servicio_id] += 1

    servicio_top = None
    if serv_count:
        top_id = max(serv_count, key=lambda x: serv_count[x])
        s = db.get(Servicio, top_id)
        if s:
            servicio_top = {
                "nombre":   s.nombre,
                "cantidad": serv_count[top_id],
            }

    # ── Alertas automáticas ───────────────────────────────────────────────────
    alertas = []
    if tasa_ausencia > 20:
        alertas.append({
            "tipo": "warning",
            "mensaje": f"Tasa de ausencias alta: {tasa_ausencia}%. "
                       f"Revisá los recordatorios automáticos."
        })
    if facturacion_ant > 0 and variacion(facturacion_bruta, facturacion_ant) < -15:
        alertas.append({
            "tipo": "danger",
            "mensaje": f"Facturación bajó {abs(variacion(facturacion_bruta, facturacion_ant))}% "
                       f"vs el período anterior."
        })
    clientes_inactivos = db.query(Cliente).filter(
        Cliente.empresa_id == empresa_id,
        Cliente.ultima_visita < datetime.now(timezone.utc) - timedelta(days=60),
        Cliente.total_visitas >= 3,
    ).count()
    if clientes_inactivos > 0:
        alertas.append({
            "tipo": "info",
            "mensaje": f"{clientes_inactivos} clientes frecuentes no vienen hace más de 60 días. "
                       f"Buen momento para una campaña de recuperación."
        })

    return {
        "periodo":     {"desde": str(desde), "hasta": str(hasta), "nombre": periodo},
        "facturacion": {
            "bruta":          round(facturacion_bruta, 2),
            "neta":           round(facturacion_neta, 2),
            "comisiones":     round(comisiones_pagadas, 2),
            "variacion_pct":  variacion(facturacion_bruta, facturacion_ant),
            "ticket_promedio": round(ticket_prom, 2),
        },
        "turnos": {
            "total":             total,
            "atendidos":         atendidos,
            "ausentes":          ausentes,
            "cancelados":        cancelados,
            "tasa_ausencia_pct": tasa_ausencia,
            "tasa_cancelacion_pct": tasa_cancelacion,
            "variacion_pct":     variacion(atendidos, atendidos_ant),
        },
        "clientes": {
            "unicos_periodo": len(ids_clientes),
            "nuevos":         clientes_nuevos,
            "recurrentes":    len(ids_clientes) - clientes_nuevos,
        },
        "top": {
            "trabajador": trabajador_top,
            "servicio":   servicio_top,
        },
        "alertas": alertas,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HEATMAP — ocupación por franja horaria
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/heatmap", summary="Heatmap de ocupación por hora y día")
def heatmap_ocupacion(
    db: DBSession,
    current_user: AdminUser,
    semanas: int = Query(8, ge=1, le=52, description="Semanas a analizar (default: 8)"),
    trabajador_id: Optional[str] = Query(None),
):
    """
    Calcula el % de ocupación por hora del día y día de la semana.

    Con 8 semanas de datos, el heatmap muestra patrones reales:
    - Qué horas siempre están llenas (picos)
    - Qué horas siempre están vacías (baches)
    - Qué días son más productivos

    Base de datos para:
    - Dynamic pricing (subir precio en picos)
    - Campañas en baches (descuento para llenar)
    - Contratación (si siempre hay baches el martes, ¿necesitan ese día?)
    """
    empresa_id = current_user.empresa_id
    desde = date.today() - timedelta(weeks=semanas)

    query = db.query(Turno).filter(
        Turno.empresa_id == empresa_id,
        Turno.fecha >= desde,
        Turno.estado == EstadoTurno.ATENDIDO,
    )

    if trabajador_id:
        query = query.filter(Turno.trabajador_id == trabajador_id)

    turnos = query.all()

    DIAS  = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    HORAS = list(range(7, 21))  # 7am a 20pm

    # Contamos turnos por día-hora
    conteo: dict = defaultdict(int)
    for t in turnos:
        if t.hora_inicio:
            dia_idx = t.fecha.weekday()
            hora    = t.hora_inicio.hour
            conteo[(dia_idx, hora)] += 1

    # Calculamos el máximo para normalizar
    max_val = max(conteo.values()) if conteo else 1

    # Construimos la matriz
    matriz = []
    for d_idx, dia in enumerate(DIAS):
        fila = {"dia": dia, "horas": {}}
        for hora in HORAS:
            cant = conteo.get((d_idx, hora), 0)
            pct  = round(cant / max_val * 100) if max_val > 0 else 0
            fila["horas"][f"{hora:02d}:00"] = {
                "cantidad": cant,
                "ocupacion_pct": pct,
            }
        matriz.append(fila)

    # Hora y día pico
    hora_pico = None
    dia_pico  = None
    if conteo:
        pico_key  = max(conteo, key=lambda x: conteo[x])
        hora_pico = f"{pico_key[1]:02d}:00"
        dia_pico  = DIAS[pico_key[0]]

    # Horas con menos del 20% de ocupación (baches para campañas)
    baches = []
    for (d_idx, hora), cant in conteo.items():
        if cant / max_val < 0.2 and cant > 0:
            baches.append({
                "dia":  DIAS[d_idx],
                "hora": f"{hora:02d}:00",
                "ocupacion_pct": round(cant / max_val * 100),
            })

    return {
        "semanas_analizadas": semanas,
        "total_turnos_analizados": len(turnos),
        "horas":   [f"{h:02d}:00" for h in HORAS],
        "dias":    DIAS,
        "matriz":  matriz,
        "hora_pico": hora_pico,
        "dia_pico":  dia_pico,
        "baches_oportunidad": sorted(baches, key=lambda x: x["ocupacion_pct"])[:5],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FACTURACIÓN — evolución temporal de ingresos
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/facturacion", summary="Evolución de facturación")
def evolucion_facturacion(
    db: DBSession,
    current_user: AdminUser,
    periodo: str = Query("mes", description="semana | mes | trimestre | año"),
    agrupacion: str = Query("dia", description="dia | semana | mes"),
):
    """
    Evolución de la facturación en el tiempo.
    Incluye comparación vs período anterior para ver tendencia.

    Ideal para el gráfico de área/línea del dashboard.
    Cada punto incluye: bruto, neto, comisiones, cantidad de pagos.
    """
    empresa_id = current_user.empresa_id
    desde, hasta = get_rango(periodo)
    desde_ant, hasta_ant = periodo_anterior(desde, hasta)

    pagos = db.query(Pago).filter(
        Pago.empresa_id == empresa_id,
        Pago.estado == EstadoPago.PAGADO,
        func.date(Pago.created_at) >= desde,
        func.date(Pago.created_at) <= hasta,
    ).all()

    # Agrupamos por día
    por_dia: dict = defaultdict(lambda: {"bruto": 0.0, "neto": 0.0, "comision": 0.0, "cantidad": 0})
    for p in pagos:
        dia = str(p.created_at.date())
        por_dia[dia]["bruto"]    += p.monto_bruto
        por_dia[dia]["neto"]     += p.monto_neto
        por_dia[dia]["comision"] += p.comision_monto
        por_dia[dia]["cantidad"] += 1

    # Rellenamos días sin pagos con cero
    delta = hasta - desde
    serie = []
    for i in range(delta.days + 1):
        dia = str(desde + timedelta(days=i))
        d   = por_dia.get(dia, {"bruto": 0.0, "neto": 0.0, "comision": 0.0, "cantidad": 0})
        serie.append({
            "fecha":    dia,
            "bruto":    round(d["bruto"], 2),
            "neto":     round(d["neto"], 2),
            "comision": round(d["comision"], 2),
            "cantidad": d["cantidad"],
        })

    # Proyección del mes: extrapolamos la tendencia
    dias_con_pagos = [d for d in serie if d["bruto"] > 0]
    proyeccion = None
    if dias_con_pagos and periodo == "mes":
        promedio_dia = sum(d["bruto"] for d in dias_con_pagos) / len(dias_con_pagos)
        dias_restantes = (hasta.replace(month=hasta.month % 12 + 1, day=1) - timedelta(days=1) - hasta).days
        proyeccion = {
            "acumulado_actual":  round(sum(d["bruto"] for d in serie), 2),
            "proyeccion_total":  round(sum(d["bruto"] for d in serie) + promedio_dia * dias_restantes, 2),
            "dias_restantes":    dias_restantes,
            "promedio_dia":      round(promedio_dia, 2),
        }

    # Totales período anterior para comparación
    total_actual   = sum(p.monto_bruto for p in pagos)
    pagos_ant      = db.query(Pago).filter(
        Pago.empresa_id == empresa_id,
        Pago.estado == EstadoPago.PAGADO,
        func.date(Pago.created_at) >= desde_ant,
        func.date(Pago.created_at) <= hasta_ant,
    ).all()
    total_anterior = sum(p.monto_bruto for p in pagos_ant)
    variacion      = round((total_actual - total_anterior) / total_anterior * 100, 1) if total_anterior > 0 else 0.0

    return {
        "periodo":          {"desde": str(desde), "hasta": str(hasta)},
        "serie":            serie,
        "totales":          {
            "bruto":    round(total_actual, 2),
            "neto":     round(sum(p.monto_neto for p in pagos), 2),
            "comision": round(sum(p.comision_monto for p in pagos), 2),
        },
        "comparacion_anterior": {
            "total":      round(total_anterior, 2),
            "variacion_pct": variacion,
            "tendencia":  "subiendo" if variacion > 0 else "bajando" if variacion < 0 else "estable",
        },
        "proyeccion_mes": proyeccion,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICIOS — ranking y análisis del catálogo
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/servicios", summary="Ranking de servicios")
def ranking_servicios(
    db: DBSession,
    current_user: AdminUser,
    periodo: str = Query("mes"),
):
    """
    Ranking de servicios por cantidad y por facturación.

    Detecta:
    - El servicio estrella (más pedido)
    - El servicio más rentable (mayor ticket)
    - Servicios que nadie pide (candidatos a eliminar o relanzar)
    - Servicios con mayor potencial (buenos notas, pocos pedidos)
    """
    empresa_id = current_user.empresa_id
    desde, hasta = get_rango(periodo)

    turnos = db.query(Turno).filter(
        Turno.empresa_id == empresa_id,
        Turno.fecha >= desde,
        Turno.fecha <= hasta,
        Turno.estado == EstadoTurno.ATENDIDO,
    ).all()

    serv_data: dict = defaultdict(lambda: {"cantidad": 0, "facturacion": 0.0, "calificaciones": []})
    for t in turnos:
        if t.servicio_id:
            serv_data[t.servicio_id]["cantidad"]    += 1
            serv_data[t.servicio_id]["facturacion"] += t.precio_final or 0.0

    servicios_activos = db.query(Servicio).filter(
        Servicio.empresa_id == empresa_id,
        Servicio.activo == True,
    ).all()

    ranking = []
    for s in servicios_activos:
        d = serv_data.get(s.id, {"cantidad": 0, "facturacion": 0.0})
        ranking.append({
            "id":           str(s.id),
            "nombre":       s.nombre,
            "precio":       s.precio_vigente,
            "duracion_min": s.duracion_minutos,
            "cantidad":     d["cantidad"],
            "facturacion":  round(d["facturacion"], 2),
            "ticket_real":  round(d["facturacion"] / d["cantidad"], 2) if d["cantidad"] > 0 else 0.0,
        })

    ranking_cantidad     = sorted(ranking, key=lambda x: x["cantidad"],    reverse=True)
    ranking_facturacion  = sorted(ranking, key=lambda x: x["facturacion"], reverse=True)
    sin_demanda          = [s for s in ranking if s["cantidad"] == 0]

    return {
        "periodo":             {"desde": str(desde), "hasta": str(hasta)},
        "por_cantidad":        ranking_cantidad,
        "por_facturacion":     ranking_facturacion,
        "sin_demanda":         sin_demanda,
        "total_servicios":     len(servicios_activos),
        "servicios_con_venta": len([s for s in ranking if s["cantidad"] > 0]),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TRABAJADORES — performance del staff
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/trabajadores", summary="Performance del staff")
def performance_trabajadores(
    db: DBSession,
    current_user: AdminUser,
    periodo: str = Query("mes"),
):
    """
    Análisis completo de performance de cada trabajador.

    Incluye: facturación, ticket promedio, cantidad de turnos,
    tasa de ausencias, calificación promedio y hora más productiva.

    Base de datos para el ranking gamificado del staff.
    """
    empresa_id = current_user.empresa_id
    desde, hasta = get_rango(periodo)

    trabajadores = db.query(Trabajador).filter(
        Trabajador.empresa_id == empresa_id,
        Trabajador.activo == True,
    ).all()

    resultado = []
    for trab in trabajadores:
        turnos_periodo = db.query(Turno).filter(
            Turno.empresa_id == empresa_id,
            Turno.trabajador_id == trab.id,
            Turno.fecha >= desde,
            Turno.fecha <= hasta,
        ).all()

        atendidos  = [t for t in turnos_periodo if t.estado == EstadoTurno.ATENDIDO]
        ausentes   = [t for t in turnos_periodo if t.estado == EstadoTurno.AUSENTE]

        pagos_trab = db.query(Pago).filter(
            Pago.empresa_id == empresa_id,
            Pago.trabajador_id == trab.id,
            Pago.estado == EstadoPago.PAGADO,
            func.date(Pago.created_at) >= desde,
            func.date(Pago.created_at) <= hasta,
        ).all()

        facturacion = sum(p.monto_bruto for p in pagos_trab)
        ticket_prom = facturacion / len(pagos_trab) if pagos_trab else 0.0
        tasa_ausencia = round(len(ausentes) / len(turnos_periodo) * 100, 1) if turnos_periodo else 0.0

        # Hora más productiva del trabajador
        hora_count: dict = defaultdict(int)
        for t in atendidos:
            if t.hora_inicio:
                hora_count[t.hora_inicio.hour] += 1
        hora_pico = f"{max(hora_count, key=hora_count.get):02d}:00" if hora_count else None

        resultado.append({
            "id":              str(trab.id),
            "nombre":          f"{trab.nombre} {trab.apellido or ''}".strip(),
            "color_agenda":    trab.color_agenda,
            "turnos_total":    len(turnos_periodo),
            "turnos_atendidos": len(atendidos),
            "turnos_ausentes": len(ausentes),
            "tasa_ausencia_pct": tasa_ausencia,
            "facturacion":     round(facturacion, 2),
            "ticket_promedio": round(ticket_prom, 2),
            "calificacion":    trab.calificacion_promedio,
            "hora_pico":       hora_pico,
        })

    # Ordenamos por facturación
    resultado.sort(key=lambda x: x["facturacion"], reverse=True)
    for i, r in enumerate(resultado):
        r["ranking"] = i + 1

    return {
        "periodo":       {"desde": str(desde), "hasta": str(hasta)},
        "trabajadores":  resultado,
        "total_staff":   len(trabajadores),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENTES — análisis de la base de clientes
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/clientes", summary="Análisis de clientes")
def analisis_clientes(
    db: DBSession,
    current_user: AdminUser,
    periodo: str = Query("mes"),
):
    """
    Análisis profundo de la base de clientes.

    Detecta: nuevos, recurrentes, en riesgo, perdidos.
    Distribución por nivel de fidelización.
    Top clientes por facturación de todos los tiempos.
    """
    empresa_id = current_user.empresa_id
    desde, hasta = get_rango(periodo)
    hoy = date.today()

    # Total de clientes
    total_clientes = db.query(Cliente).filter(
        Cliente.empresa_id == empresa_id,
    ).count()

    # Distribución por nivel de fidelización
    niveles = {}
    for nivel in NivelFidelizacion:
        count = db.query(Cliente).filter(
            Cliente.empresa_id == empresa_id,
            Cliente.nivel_fidelizacion == nivel,
        ).count()
        niveles[nivel.value] = count

    # Clientes activos del período
    turnos_periodo = db.query(Turno).filter(
        Turno.empresa_id == empresa_id,
        Turno.fecha >= desde,
        Turno.fecha <= hasta,
        Turno.estado == EstadoTurno.ATENDIDO,
    ).all()

    ids_activos  = {t.cliente_id for t in turnos_periodo}
    clientes_nuevos_periodo = sum(
        1 for cid in ids_activos
        if db.query(Turno).filter(
            Turno.cliente_id == cid,
            Turno.fecha < desde,
            Turno.estado == EstadoTurno.ATENDIDO,
        ).count() == 0
    )

    # En riesgo: frecuentes que no vienen hace 30-60 días
    limite_riesgo  = datetime.now(timezone.utc) - timedelta(days=45)
    limite_perdido = datetime.now(timezone.utc) - timedelta(days=90)

    en_riesgo = db.query(Cliente).filter(
        Cliente.empresa_id == empresa_id,
        Cliente.total_visitas >= 3,
        Cliente.ultima_visita < limite_riesgo,
        Cliente.ultima_visita >= limite_perdido,
    ).count()

    perdidos = db.query(Cliente).filter(
        Cliente.empresa_id == empresa_id,
        Cliente.total_visitas >= 3,
        Cliente.ultima_visita < limite_perdido,
    ).count()

    # Top 10 clientes por facturación total
    top_clientes = db.query(Cliente).filter(
        Cliente.empresa_id == empresa_id,
    ).order_by(Cliente.total_gastado.desc()).limit(10).all()

    top_list = [
        {
            "id":            str(c.id),
            "nombre":        f"{c.nombre} {c.apellido or ''}".strip(),
            "total_gastado": c.total_gastado,
            "total_visitas": c.total_visitas,
            "nivel":         c.nivel_fidelizacion.value,
            "ultima_visita": str(c.ultima_visita.date()) if c.ultima_visita else None,
        }
        for c in top_clientes
    ]

    return {
        "periodo":        {"desde": str(desde), "hasta": str(hasta)},
        "resumen": {
            "total_clientes":    total_clientes,
            "activos_periodo":   len(ids_activos),
            "nuevos_periodo":    clientes_nuevos_periodo,
            "recurrentes":       len(ids_activos) - clientes_nuevos_periodo,
            "en_riesgo":         en_riesgo,
            "perdidos":          perdidos,
            "tasa_retencion_pct": round(
                (len(ids_activos) - clientes_nuevos_periodo) / len(ids_activos) * 100, 1
            ) if ids_activos else 0.0,
        },
        "por_nivel": niveles,
        "top_clientes": top_list,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AUSENCIAS — análisis de no-shows
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/ausencias", summary="Análisis de no-shows")
def analisis_ausencias(
    db: DBSession,
    current_user: AdminUser,
    semanas: int = Query(12, ge=1, le=52),
):
    """
    Análisis profundo de las ausencias para el predictor de IA.

    Encuentra los patrones reales de no-show:
    - Qué días y horas tienen más ausencias
    - Qué tipo de cliente falta más
    - Cuánto dinero se perdió por ausencias
    - Los clientes con más ausencias acumuladas
    """
    empresa_id = current_user.empresa_id
    desde = date.today() - timedelta(weeks=semanas)

    turnos_ausentes = db.query(Turno).filter(
        Turno.empresa_id == empresa_id,
        Turno.fecha >= desde,
        Turno.estado == EstadoTurno.AUSENTE,
    ).all()

    todos_turnos = db.query(Turno).filter(
        Turno.empresa_id == empresa_id,
        Turno.fecha >= desde,
        Turno.estado.in_([EstadoTurno.ATENDIDO, EstadoTurno.AUSENTE]),
    ).count()

    tasa_global = round(len(turnos_ausentes) / todos_turnos * 100, 1) if todos_turnos > 0 else 0.0

    # Por día de la semana
    DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    por_dia: dict = defaultdict(int)
    for t in turnos_ausentes:
        por_dia[t.fecha.weekday()] += 1

    # Por hora
    por_hora: dict = defaultdict(int)
    for t in turnos_ausentes:
        if t.hora_inicio:
            por_hora[t.hora_inicio.hour] += 1

    # Dinero perdido estimado
    dinero_perdido = sum(t.precio_final or 0.0 for t in turnos_ausentes)

    # Top clientes ausentes
    cliente_ausencias: dict = defaultdict(int)
    for t in turnos_ausentes:
        if t.cliente_id:
            cliente_ausencias[t.cliente_id] += 1

    top_ausentes = []
    for cid, count in sorted(cliente_ausencias.items(), key=lambda x: x[1], reverse=True)[:5]:
        c = db.get(Cliente, cid)
        if c:
            top_ausentes.append({
                "nombre":   f"{c.nombre} {c.apellido or ''}".strip(),
                "ausencias": count,
                "nivel":    c.nivel_fidelizacion.value,
            })

    return {
        "semanas_analizadas":   semanas,
        "total_ausencias":      len(turnos_ausentes),
        "tasa_global_pct":      tasa_global,
        "dinero_perdido_estimado": round(dinero_perdido, 2),
        "por_dia_semana": [
            {"dia": DIAS[i], "cantidad": por_dia.get(i, 0)}
            for i in range(7)
        ],
        "por_hora": [
            {"hora": f"{h:02d}:00", "cantidad": por_hora.get(h, 0)}
            for h in range(7, 21)
        ],
        "top_clientes_ausentes": top_ausentes,
        "dia_mas_ausencias":  DIAS[max(por_dia, key=por_dia.get)] if por_dia else None,
        "hora_mas_ausencias": f"{max(por_hora, key=por_hora.get):02d}:00" if por_hora else None,
    }