'use client'
 
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { trabajadoresApi, estadisticasApi } from '@/lib/api'
import { Trabajador } from '@/types'
import { motion } from 'framer-motion'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  Plus, Star, TrendingUp, UserCog, Crown, Medal,
  Award, Clock, Target, AlertTriangle, Zap, Flame
} from 'lucide-react'
 
const qc = new QueryClient()
export default function TrabajadoresPage() {
  return <QueryClientProvider client={qc}><Trabajadores /></QueryClientProvider>
}
 
const DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
const DIAS_KEY = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
 
interface PerfStats {
  id: string
  nombre: string
  color_agenda: string
  turnos_total: number
  turnos_atendidos: number
  turnos_ausentes: number
  tasa_ausencia_pct: number
  facturacion: number
  ticket_promedio: number
  calificacion: number
  hora_pico: string | null
  ranking: number
}
 
// ─── Generar insight automático ───────────────────────────────────────────────
function generarInsight(p: PerfStats, promedio: number): { texto: string; color: string; icon: React.ElementType } | null {
  if (p.facturacion === 0) return null
  if (p.facturacion > promedio * 1.3)
    return { texto: `Genera ${Math.round((p.facturacion / promedio - 1) * 100)}% más que el promedio del equipo`, color: '#10b981', icon: Flame }
  if (p.tasa_ausencia_pct > 25)
    return { texto: `Tasa de ausencias alta (${p.tasa_ausencia_pct}%) — revisar recordatorios de sus clientes`, color: '#ef4444', icon: AlertTriangle }
  if (p.ticket_promedio > promedio * 1.2 && promedio > 0)
    return { texto: `Ticket promedio alto — bueno vendiendo servicios premium`, color: '#8b5cf6', icon: TrendingUp }
  if (p.hora_pico)
    return { texto: `Su mejor horario es a las ${p.hora_pico}`, color: '#3b82f6', icon: Clock }
  return null
}
 
// ─── Podio (top 3) ────────────────────────────────────────────────────────────
function Podio({ top }: { top: PerfStats[] }) {
  if (top.length === 0) return null
  const medallas = [
    { icon: Crown, color: '#f59e0b', bg: '#fffbeb', label: '1°', altura: 'h-24' },
    { icon: Medal, color: '#94a3b8', bg: '#f8fafc', label: '2°', altura: 'h-20' },
    { icon: Award, color: '#d97706', bg: '#fffbeb', label: '3°', altura: 'h-16' },
  ]
  // Orden visual: 2°, 1°, 3°
  const orden = [top[1], top[0], top[2]].filter(Boolean)
  const medallaDe = (p: PerfStats) => medallas[p.ranking - 1] || medallas[2]
 
  return (
    <div className="rounded-2xl p-6 mb-6" style={{ background: 'var(--color-navy)', border: '1px solid rgba(255,255,255,0.06)' }}>
      <p className="text-xs font-semibold uppercase tracking-widest mb-5 text-center" style={{ color: 'rgba(255,255,255,0.4)' }}>
        🏆 Ranking del mes
      </p>
      <div className="flex items-end justify-center gap-4">
        {orden.map((p) => {
          const m = medallaDe(p)
          return (
            <motion.div key={p.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: p.ranking * 0.1 }}
              className="flex flex-col items-center" style={{ width: '120px' }}>
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-xl font-bold mb-2 relative"
                style={{ background: `${p.color_agenda}20`, color: p.color_agenda, border: `2px solid ${p.color_agenda}`, fontFamily: 'var(--font-display)' }}>
                {p.nombre.charAt(0)}
                <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full flex items-center justify-center"
                  style={{ background: m.bg, border: `2px solid ${m.color}` }}>
                  <m.icon size={12} style={{ color: m.color }} />
                </div>
              </div>
              <p className="text-sm font-semibold text-white text-center leading-tight mb-0.5">{p.nombre}</p>
              <p className="text-xs mb-2" style={{ color: 'var(--color-teal)' }}>
                ${(p.facturacion / 1000).toFixed(1)}k
              </p>
              <div className={`w-full ${m.altura} rounded-t-xl flex items-start justify-center pt-2`}
                style={{ background: `linear-gradient(180deg, ${p.color_agenda}40, ${p.color_agenda}10)`, border: `1px solid ${p.color_agenda}30`, borderBottom: 'none' }}>
                <span className="text-lg font-bold" style={{ color: p.color_agenda, fontFamily: 'var(--font-display)' }}>{m.label}</span>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
 
// ─── Tarjeta de performance ───────────────────────────────────────────────────
function TrabajadorPerfCard({ t, stats, maxFacturacion, promedioFacturacion }: {
  t: Trabajador
  stats?: PerfStats
  maxFacturacion: number
  promedioFacturacion: number
}) {
  const fact = stats?.facturacion || 0
  const pctBarra = maxFacturacion > 0 ? (fact / maxFacturacion) * 100 : 0
  const insight = stats ? generarInsight(stats, promedioFacturacion) : null
 
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl p-5"
      style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderLeft: `4px solid ${t.color_agenda}` }}>
 
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-lg font-bold shrink-0 relative"
          style={{ background: `${t.color_agenda}18`, color: t.color_agenda, border: `1.5px solid ${t.color_agenda}40`, fontFamily: 'var(--font-display)' }}>
          {t.nombre.charAt(0).toUpperCase()}
          {stats && stats.ranking <= 3 && fact > 0 && (
            <div className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold"
              style={{ background: stats.ranking === 1 ? '#fbbf24' : stats.ranking === 2 ? '#cbd5e1' : '#d97706', color: 'white' }}>
              {stats.ranking}
            </div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm" style={{ color: 'var(--color-text-1)' }}>
            {t.nombre} {t.apellido || ''}
          </p>
          {t.especialidades?.length > 0 && (
            <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--color-text-3)' }}>
              {t.especialidades.join(' · ')}
            </p>
          )}
        </div>
        {t.calificacion_promedio > 0 && (
          <div className="flex items-center gap-1 px-2 py-1 rounded-lg shrink-0" style={{ background: '#fffbeb' }}>
            <Star size={11} style={{ color: '#f59e0b', fill: '#f59e0b' }} />
            <span className="text-xs font-semibold" style={{ color: '#f59e0b' }}>{t.calificacion_promedio.toFixed(1)}</span>
          </div>
        )}
      </div>
 
      {/* Facturación con barra comparativa */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs font-medium" style={{ color: 'var(--color-text-3)' }}>Facturación del mes</span>
          <span className="text-sm font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-teal)' }}>
            ${fact.toLocaleString('es-AR')}
          </span>
        </div>
        <div className="h-2 rounded-full overflow-hidden" style={{ background: 'var(--color-bg)' }}>
          <motion.div className="h-full rounded-full" style={{ background: t.color_agenda }}
            initial={{ width: 0 }} animate={{ width: `${pctBarra}%` }} transition={{ duration: 0.8 }} />
        </div>
      </div>
 
      {/* Métricas */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="rounded-xl p-2.5 text-center" style={{ background: 'var(--color-bg)' }}>
          <p className="text-base font-bold leading-none mb-0.5" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
            {stats?.turnos_atendidos || 0}
          </p>
          <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>atendidos</p>
        </div>
        <div className="rounded-xl p-2.5 text-center" style={{ background: 'var(--color-bg)' }}>
          <p className="text-base font-bold leading-none mb-0.5" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
            ${((stats?.ticket_promedio || 0) / 1000).toFixed(1)}k
          </p>
          <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>ticket</p>
        </div>
        <div className="rounded-xl p-2.5 text-center" style={{ background: (stats?.tasa_ausencia_pct || 0) > 20 ? '#fef2f2' : 'var(--color-bg)' }}>
          <p className="text-base font-bold leading-none mb-0.5" style={{ fontFamily: 'var(--font-display)', color: (stats?.tasa_ausencia_pct || 0) > 20 ? '#ef4444' : 'var(--color-text-1)' }}>
            {stats?.tasa_ausencia_pct || 0}%
          </p>
          <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>ausencias</p>
        </div>
      </div>
 
      {/* Insight automático */}
      {insight && (
        <div className="flex items-start gap-2 px-3 py-2 rounded-xl mb-4"
          style={{ background: `${insight.color}10`, border: `1px solid ${insight.color}25` }}>
          <insight.icon size={13} className="mt-0.5 shrink-0" style={{ color: insight.color }} />
          <p className="text-xs" style={{ color: insight.color }}>{insight.texto}</p>
        </div>
      )}
 
      {/* Días que trabaja */}
      <div className="flex items-center gap-1.5">
        {DIAS.map((dia, i) => {
          const trabaja = t.horarios?.[DIAS_KEY[i]]?.activo
          return (
            <div key={dia} className="flex-1 text-center py-1.5 rounded-lg text-xs font-medium"
              style={{ background: trabaja ? `${t.color_agenda}15` : 'var(--color-bg)', color: trabaja ? t.color_agenda : 'var(--color-text-3)' }}>
              {dia}
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}
 
function Trabajadores() {
  const [periodo, setPeriodo] = useState('mes')
 
  const { data: trabajadores, isLoading } = useQuery<Trabajador[]>({
    queryKey: ['trabajadores'],
    queryFn: () => trabajadoresApi.listar().then(r => r.data),
  })
 
  const { data: perfData } = useQuery({
    queryKey: ['trabajadores-perf', periodo],
    queryFn: () => estadisticasApi.trabajadores(periodo).then(r => r.data),
  })
 
  const lista = trabajadores || []
  const statsArr: PerfStats[] = perfData?.trabajadores || []
  const statsMap = Object.fromEntries(statsArr.map(s => [s.id, s]))
 
  const maxFact = Math.max(...statsArr.map(s => s.facturacion), 1)
  const conFacturacion = statsArr.filter(s => s.facturacion > 0)
  const promedioFact = conFacturacion.length > 0
    ? conFacturacion.reduce((sum, s) => sum + s.facturacion, 0) / conFacturacion.length
    : 0
  const top3 = statsArr.filter(s => s.facturacion > 0).slice(0, 3)
  const facturacionTotal = statsArr.reduce((sum, s) => sum + s.facturacion, 0)
 
  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
            Equipo
          </h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--color-text-3)' }}>
            {lista.filter(t => t.activo).length} profesionales · ${facturacionTotal.toLocaleString('es-AR')} generados este mes
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select value={periodo} onChange={e => setPeriodo(e.target.value)}
            className="h-10 px-3 rounded-xl text-sm outline-none cursor-pointer"
            style={{ background: 'var(--color-surface)', border: '1.5px solid var(--color-border)', color: 'var(--color-text-2)' }}>
            <option value="semana">Esta semana</option>
            <option value="mes">Este mes</option>
            <option value="año">Este año</option>
          </select>
          <button className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold"
            style={{ background: 'var(--color-teal)', color: 'var(--color-navy)', fontFamily: 'var(--font-display)' }}>
            <Plus size={16} /> Nuevo
          </button>
        </div>
      </div>
 
      {/* Podio */}
      {top3.length >= 2 && <Podio top={top3} />}
 
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1,2].map(i => <div key={i} className="h-64 rounded-2xl animate-pulse" style={{ background: 'var(--color-border)' }} />)}
        </div>
      ) : lista.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
            style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
            <UserCog size={28} style={{ color: 'var(--color-text-3)' }} />
          </div>
          <p className="font-semibold" style={{ color: 'var(--color-text-2)' }}>Sin trabajadores todavía</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 stagger">
          {lista.map(t => (
            <TrabajadorPerfCard key={t.id} t={t} stats={statsMap[t.id]}
              maxFacturacion={maxFact} promedioFacturacion={promedioFact} />
          ))}
        </div>
      )}
    </div>
  )
}