'use client'
 
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/store/auth'
import { estadisticasApi, turnosApi } from '@/lib/api'
import { ResumenDashboard, Turno } from '@/types'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Calendar, Banknote, UserCheck, AlertTriangle, Info, ArrowUpRight, Clock } from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
 
const qc = new QueryClient()
 
export default function DashboardPage() {
  return (
    <QueryClientProvider client={qc}>
      <Dashboard />
    </QueryClientProvider>
  )
}
 
function StatCard({ label, value, sub, trend, icon: Icon, color, delay = 0 }: {
  label: string; value: string; sub?: string; trend?: number
  icon: React.ElementType; color: string; delay?: number
}) {
  const up = (trend ?? 0) >= 0
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.4 }}
      className="rounded-2xl p-5" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${color}18`, border: `1px solid ${color}30` }}>
          <Icon size={18} style={{ color }} />
        </div>
        {trend !== undefined && (
          <div className="flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full"
            style={{ background: up ? 'var(--color-success-bg)' : 'var(--color-danger-bg)', color: up ? 'var(--color-success)' : 'var(--color-danger)' }}>
            {up ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
            {Math.abs(trend).toFixed(1)}%
          </div>
        )}
      </div>
      <p className="text-2xl font-bold mb-1" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>{value}</p>
      <p className="text-sm font-medium" style={{ color: 'var(--color-text-2)' }}>{label}</p>
      {sub && <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-3)' }}>{sub}</p>}
    </motion.div>
  )
}
 
function TurnoItem({ turno }: { turno: Turno }) {
  const cfg: Record<string, { label: string; color: string; bg: string }> = {
    pendiente:  { label: 'Pendiente',  color: '#f59e0b', bg: '#fffbeb' },
    confirmado: { label: 'Confirmado', color: '#10b981', bg: '#ecfdf5' },
    atendido:   { label: 'Atendido',   color: '#3b82f6', bg: '#eff6ff' },
    cancelado:  { label: 'Cancelado',  color: '#ef4444', bg: '#fef2f2' },
    ausente:    { label: 'Ausente',    color: '#ef4444', bg: '#fef2f2' },
  }
  const c = cfg[turno.estado] || cfg.pendiente
  return (
    <div className="flex items-center gap-4 py-3 px-4 rounded-xl cursor-pointer" style={{ border: '1px solid transparent' }}>
      <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 text-sm font-bold"
        style={{ background: 'var(--color-navy)', color: 'var(--color-teal)', fontFamily: 'var(--font-display)' }}>
        {turno.hora_inicio.slice(0, 5)}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold truncate" style={{ color: 'var(--color-text-1)' }}>{turno.cliente_nombre || 'Cliente'}</p>
        <p className="text-xs truncate" style={{ color: 'var(--color-text-3)' }}>{turno.servicio_nombre} · {turno.trabajador_nombre}</p>
      </div>
      <span className="text-xs font-medium px-2.5 py-1 rounded-full shrink-0" style={{ background: c.bg, color: c.color }}>{c.label}</span>
    </div>
  )
}
 
function AlertItem({ tipo, mensaje }: { tipo: string; mensaje: string }) {
  const cfg: Record<string, { icon: React.ElementType; color: string; bg: string }> = {
    warning: { icon: AlertTriangle, color: '#f59e0b', bg: '#fffbeb' },
    danger:  { icon: AlertTriangle, color: '#ef4444', bg: '#fef2f2' },
    info:    { icon: Info,          color: '#3b82f6', bg: '#eff6ff' },
  }
  const c = cfg[tipo] || cfg.info
  return (
    <div className="flex items-start gap-3 p-4 rounded-xl text-sm" style={{ background: c.bg, border: `1px solid ${c.color}25` }}>
      <c.icon size={16} className="shrink-0 mt-0.5" style={{ color: c.color }} />
      <span style={{ color: 'var(--color-text-2)' }}>{mensaje}</span>
    </div>
  )
}
 
function Dashboard() {
  const { user } = useAuthStore()
  const [periodo, setPeriodo] = useState('mes')
  const hoy = format(new Date(), "EEEE d 'de' MMMM", { locale: es })
 
  const labelPeriodo = periodo === 'hoy' ? 'de hoy' : periodo === 'semana' ? 'semanal' : periodo === 'año' ? 'del año' : 'del mes'
 
  const { data: resumen } = useQuery<ResumenDashboard>({
    queryKey: ['resumen', periodo],
    queryFn: () => estadisticasApi.resumen(periodo).then((r) => r.data),
    refetchInterval: 60000,
  })
 
  const { data: turnosHoy } = useQuery<{ items: Turno[] }>({
    queryKey: ['turnos-hoy'],
    queryFn: () => turnosApi.listar({ fecha: format(new Date(), 'yyyy-MM-dd'), por_pagina: 20 }).then((r) => r.data),
    refetchInterval: 30000,
  })
 
  const f = resumen?.facturacion
  const t = resumen?.turnos
 
  return (
    <div className="p-8 max-w-7xl mx-auto">
 
      <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-1" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
            Buen día, {user?.nombre} 👋
          </h1>
          <p className="capitalize" style={{ color: 'var(--color-text-3)', fontSize: '14px' }}>{hoy}</p>
        </div>
        <div className="flex items-center gap-2">
          <select value={periodo} onChange={e => setPeriodo(e.target.value)}
            className="h-9 px-3 rounded-xl text-sm outline-none cursor-pointer"
            style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-2)' }}>
            <option value="hoy">Hoy</option>
            <option value="semana">Esta semana</option>
            <option value="mes">Este mes</option>
            <option value="año">Este año</option>
          </select>
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium"
            style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-2)' }}>
            <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: 'var(--color-teal)' }} />
            En vivo
          </div>
        </div>
      </motion.div>
 
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-8 stagger">
        <StatCard label={`Facturación ${labelPeriodo}`} value={`$${(f?.bruta ?? 0).toLocaleString('es-AR')}`} sub={`Neto: $${(f?.neta ?? 0).toLocaleString('es-AR')}`} trend={f?.variacion_pct} icon={Banknote} color="var(--color-teal)" delay={0} />
        <StatCard label="Turnos atendidos" value={String(t?.atendidos ?? 0)} sub={`De ${t?.total ?? 0} totales`} trend={t?.variacion_pct} icon={UserCheck} color="#3b82f6" delay={0.06} />
        <StatCard label="Ticket promedio" value={`$${(f?.ticket_promedio ?? 0).toLocaleString('es-AR')}`} sub="Por turno atendido" icon={TrendingUp} color="#f59e0b" delay={0.12} />
        <StatCard label="Tasa de ausencias" value={`${t?.tasa_ausencia_pct ?? 0}%`} sub={`${t?.ausentes ?? 0} ausentes`} icon={Calendar} color={(t?.tasa_ausencia_pct ?? 0) > 20 ? '#ef4444' : '#10b981'} delay={0.18} />
      </div>
 
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
 
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="xl:col-span-2 rounded-2xl p-6" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="font-semibold text-base" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>Turnos de hoy</h2>
              <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-3)' }}>{turnosHoy?.items?.length ?? 0} turnos programados</p>
            </div>
            <a href="/agenda" className="flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg" style={{ color: 'var(--color-teal)', background: 'var(--color-teal-muted)' }}>
              Ver agenda <ArrowUpRight size={12} />
            </a>
          </div>
          {turnosHoy?.items?.length ? (
            <div className="space-y-1">
              {turnosHoy.items.slice(0, 8).map((turno) => (<TurnoItem key={turno.id} turno={turno} />))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 rounded-xl" style={{ background: 'var(--color-bg)' }}>
              <Clock size={32} className="mb-3" style={{ color: 'var(--color-text-3)' }} />
              <p className="text-sm font-medium" style={{ color: 'var(--color-text-2)' }}>Sin turnos para hoy</p>
              <p className="text-xs mt-1" style={{ color: 'var(--color-text-3)' }}>Los turnos de hoy aparecerán acá</p>
            </div>
          )}
        </motion.div>
 
        <div className="space-y-5">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
            className="rounded-2xl p-5" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
            <h3 className="font-semibold text-sm mb-4" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>Top del período</h3>
            <div className="space-y-4">
              {resumen?.top?.trabajador && (
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-bold shrink-0"
                    style={{ background: 'rgba(0,212,170,0.1)', color: 'var(--color-teal)', border: '1px solid rgba(0,212,170,0.2)' }}>
                    {resumen.top.trabajador.nombre.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate" style={{ color: 'var(--color-text-1)' }}>{resumen.top.trabajador.nombre}</p>
                    <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>${resumen.top.trabajador.facturacion.toLocaleString('es-AR')} facturados</p>
                  </div>
                  <span className="text-xs px-2 py-1 rounded-full font-medium" style={{ background: 'var(--color-teal-muted)', color: 'var(--color-teal)' }}>#1</span>
                </div>
              )}
              {resumen?.top?.servicio && (
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-bold shrink-0"
                    style={{ background: 'rgba(59,130,246,0.1)', color: '#3b82f6', border: '1px solid rgba(59,130,246,0.2)' }}>✂</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate" style={{ color: 'var(--color-text-1)' }}>{resumen.top.servicio.nombre}</p>
                    <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>{resumen.top.servicio.cantidad} turnos</p>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
 
          {(resumen?.alertas?.length ?? 0) > 0 && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
              className="rounded-2xl p-5" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
              <h3 className="font-semibold text-sm mb-3" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>Alertas</h3>
              <div className="space-y-2">
                {resumen!.alertas.map((a, i) => <AlertItem key={i} tipo={a.tipo} mensaje={a.mensaje} />)}
              </div>
            </motion.div>
          )}
 
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}
            className="rounded-2xl p-5" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
            <h3 className="font-semibold text-sm mb-3" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>Clientes del período</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl p-3 text-center" style={{ background: 'var(--color-bg)' }}>
                <p className="text-xl font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>{resumen?.clientes?.nuevos ?? 0}</p>
                <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>Nuevos</p>
              </div>
              <div className="rounded-xl p-3 text-center" style={{ background: 'var(--color-bg)' }}>
                <p className="text-xl font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>{resumen?.clientes?.recurrentes ?? 0}</p>
                <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>Recurrentes</p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}