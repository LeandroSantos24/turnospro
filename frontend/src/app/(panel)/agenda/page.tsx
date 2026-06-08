'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { turnosApi, trabajadoresApi, clientesApi } from '@/lib/api'
import { Turno, Trabajador, Cliente } from '@/types'
import { motion, AnimatePresence } from 'framer-motion'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { format, addDays, subDays, isToday } from 'date-fns'
import { es } from 'date-fns/locale'
import {
  ChevronLeft, ChevronRight, Check, X, UserX, Clock, Scissors,
  FileText, MessageSquare, AlertCircle, Smile, Meh, Frown, Zap,
  Crown, Star, Sparkles, AlertTriangle, ChevronDown, ChevronUp,
  Gift, Phone, CalendarPlus, Info
} from 'lucide-react'

const qc = new QueryClient()
export default function AgendaPage() {
  return <QueryClientProvider client={qc}><Agenda /></QueryClientProvider>
}

// ─── Config estados ───────────────────────────────────────────────────────────
const ESTADO_CFG: Record<string, { label: string; color: string; bg: string; border: string }> = {
  pendiente:  { label: 'Pendiente',  color: '#f59e0b', bg: '#fffbeb', border: '#fcd34d' },
  confirmado: { label: 'Confirmado', color: '#10b981', bg: '#ecfdf5', border: '#6ee7b7' },
  atendido:   { label: 'Atendido',   color: '#3b82f6', bg: '#eff6ff', border: '#93c5fd' },
  cancelado:  { label: 'Cancelado',  color: '#94a3b8', bg: '#f8fafc', border: '#e2e8f0' },
  ausente:    { label: 'Ausente',    color: '#ef4444', bg: '#fef2f2', border: '#fca5a5' },
  en_curso:   { label: 'En curso',   color: '#8b5cf6', bg: '#f5f3ff', border: '#c4b5fd' },
}

const MOODS = [
  { id: 'feliz',    icon: Smile,  label: 'Bien',    color: '#10b981' },
  { id: 'normal',   icon: Meh,    label: 'Normal',  color: '#f59e0b' },
  { id: 'apurado',  icon: Zap,    label: 'Apurado', color: '#f97316' },
  { id: 'malhumor', icon: Frown,  label: 'Mal',     color: '#ef4444' },
]

// ─── Badge del nivel de cliente ───────────────────────────────────────────────
function NivelBadge({ nivel, visitas }: { nivel: string; visitas: number }) {
  const cfg: Record<string, { icon: React.ElementType; label: string; color: string; bg: string }> = {
    vip:       { icon: Crown,    label: 'VIP',       color: '#f59e0b', bg: '#fffbeb' },
    frecuente: { icon: Star,     label: 'Frecuente', color: '#8b5cf6', bg: '#f5f3ff' },
    regular:   { icon: Star,     label: 'Regular',   color: '#3b82f6', bg: '#eff6ff' },
    nuevo:     { icon: Sparkles, label: 'Nuevo',     color: '#10b981', bg: '#ecfdf5' },
  }
  const c = cfg[nivel] || cfg.nuevo
  return (
    <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium shrink-0"
      style={{ background: c.bg, color: c.color }}>
      <c.icon size={10} />
      {c.label} · {visitas} {visitas === 1 ? 'visita' : 'visitas'}
    </span>
  )
}

// ─── Modal de notas post-servicio ─────────────────────────────────────────────
function NotasModal({ onClose, onSave, onAgendarSiguiente }: {
  onClose: () => void
  onSave: (nota: string) => void
  onAgendarSiguiente: () => void
}) {
  const [nota, setNota] = useState('')
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}>
      <motion.div initial={{ opacity: 0, scale: 0.95, y: 10 }} animate={{ opacity: 1, scale: 1, y: 0 }}
        className="w-full max-w-md rounded-2xl p-6" style={{ background: 'var(--color-surface)' }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.2)' }}>
            <MessageSquare size={18} style={{ color: 'var(--color-teal)' }} />
          </div>
          <div>
            <h3 className="font-semibold text-base" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
              Notas del servicio
            </h3>
            <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>
              Aparecerán en la próxima visita 🕰️
            </p>
          </div>
        </div>
        <textarea autoFocus value={nota} onChange={e => setNota(e.target.value)}
          placeholder="Ej: Usé tijera N°4, prefiere degradado natural, trae referencia en el celu. Le gusta el fútbol..."
          rows={4} className="w-full rounded-xl p-3 text-sm resize-none outline-none mb-4"
          style={{ background: 'var(--color-bg)', border: '1.5px solid var(--color-border)', color: 'var(--color-text-1)', lineHeight: '1.6' }} />
        <div className="flex gap-2">
          <button onClick={onClose} className="py-2.5 px-4 rounded-xl text-sm font-medium"
            style={{ background: 'var(--color-bg)', color: 'var(--color-text-2)', border: '1px solid var(--color-border)' }}>
            Omitir
          </button>
          <button onClick={() => { if (nota.trim()) onSave(nota); else onClose() }}
            className="flex-1 py-2.5 rounded-xl text-sm font-bold"
            style={{ background: 'var(--color-teal)', color: 'var(--color-navy)' }}>
            Guardar nota
          </button>
          <button onClick={onAgendarSiguiente}
            className="py-2.5 px-3 rounded-xl text-sm font-medium flex items-center gap-1.5"
            style={{ background: 'var(--color-navy)', color: 'var(--color-teal)', border: '1px solid rgba(0,212,170,0.2)' }}>
            <CalendarPlus size={14} /> Próximo turno
          </button>
        </div>
      </motion.div>
    </div>
  )
}

// ─── Tarjeta de turno expandible ─────────────────────────────────────────────
function TurnoCard({ turno, trabajadorColor, cliente, onAction, onNota }: {
  turno: Turno
  trabajadorColor: string
  cliente?: Cliente
  onAction: (id: string, accion: string) => void
  onNota: (id: string) => void
}) {
  const [expandido, setExpandido] = useState(false)
  const [moodAbierto, setMoodAbierto] = useState(false)
  const [moodSeleccionado, setMoodSeleccionado] = useState<string | null>(null)

  const cfg = ESTADO_CFG[turno.estado] || ESTADO_CFG.pendiente
  const canConfirm  = turno.estado === 'pendiente'
  const canAtender  = ['confirmado', 'pendiente', 'en_curso'].includes(turno.estado)
  const canAusente  = ['confirmado', 'pendiente'].includes(turno.estado)
  const canCancelar = !['atendido', 'cancelado', 'ausente'].includes(turno.estado)
  const esAtendido  = turno.estado === 'atendido'
  const moodCfg     = moodSeleccionado ? MOODS.find(m => m.id === moodSeleccionado) : null

  // Detectar alertas especiales
  const esPrimeraVisita = cliente && cliente.total_visitas <= 1
  const esVisitaMilestone = cliente && [5, 10, 20, 50].includes(cliente.total_visitas)
  const tieneAusencias = cliente && (cliente.ausencias || 0) >= 3
  const cumpleEstesMes = cliente?.fecha_nacimiento && (() => {
    const d = new Date(cliente.fecha_nacimiento!)
    return d.getMonth() === new Date().getMonth()
  })()

  return (
    <motion.div initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
      className="rounded-2xl mb-3 overflow-hidden"
      style={{ background: 'var(--color-surface)', border: `1px solid var(--color-border)` }}>

      <div className="flex">
        {/* Franja de color trabajador */}
        <div className="w-1 shrink-0" style={{ background: trabajadorColor }} />

        <div className="flex-1 p-4">
          {/* Badges de alerta */}
          {(esPrimeraVisita || esVisitaMilestone || tieneAusencias || cumpleEstesMes) && (
            <div className="flex gap-2 flex-wrap mb-2">
              {esPrimeraVisita && (
                <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-semibold"
                  style={{ background: '#ecfdf5', color: '#10b981' }}>
                  <Sparkles size={10} /> Primera visita
                </span>
              )}
              {esVisitaMilestone && !esPrimeraVisita && (
                <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-semibold"
                  style={{ background: '#fffbeb', color: '#f59e0b' }}>
                  🎉 Visita #{cliente?.total_visitas}
                </span>
              )}
              {tieneAusencias && (
                <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-semibold"
                  style={{ background: '#fef2f2', color: '#ef4444' }}>
                  <AlertTriangle size={10} /> {cliente?.ausencias} ausencias
                </span>
              )}
              {cumpleEstesMes && (
                <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-semibold"
                  style={{ background: '#fdf4ff', color: '#a855f7' }}>
                  <Gift size={10} /> Cumple este mes
                </span>
              )}
            </div>
          )}

          <div className="flex items-start gap-3">
            {/* Hora */}
            <div className="text-center shrink-0 w-12">
              <div className="text-sm font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
                {turno.hora_inicio.slice(0, 5)}
              </div>
              <div className="text-xs" style={{ color: 'var(--color-text-3)' }}>
                {turno.hora_fin.slice(0, 5)}
              </div>
              <div className="text-xs mt-1 font-medium" style={{ color: 'var(--color-teal)' }}>
                {turno.duracion_minutos}m
              </div>
            </div>

            {/* Info principal */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start gap-2 mb-1 flex-wrap">
                <p className="font-semibold text-sm" style={{ color: 'var(--color-text-1)' }}>
                  {turno.cliente_nombre || 'Sin nombre'}
                </p>
                <span className="text-xs px-2 py-0.5 rounded-full font-medium shrink-0"
                  style={{ background: cfg.bg, color: cfg.color }}>{cfg.label}</span>
                {moodCfg && (
                  <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium shrink-0"
                    style={{ background: `${moodCfg.color}15`, color: moodCfg.color }}>
                    <moodCfg.icon size={10} /> {moodCfg.label}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3 flex-wrap mb-1">
                <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--color-text-3)' }}>
                  <Scissors size={10} /> {turno.servicio_nombre}
                </span>
                <span className="text-xs font-medium" style={{ color: 'var(--color-text-3)' }}>
                  {turno.trabajador_nombre}
                </span>
                {turno.precio_base && (
                  <span className="text-xs font-semibold" style={{ color: 'var(--color-teal)' }}>
                    ${(turno.precio_base).toLocaleString('es-AR')}
                  </span>
                )}
              </div>

              {cliente && (
                <NivelBadge nivel={cliente.nivel_fidelizacion} visitas={cliente.total_visitas} />
              )}

              {/* Cápsula de tiempo */}
              {turno.notas_cliente && (
                <div className="mt-2 flex items-start gap-1.5 px-2.5 py-1.5 rounded-lg"
                  style={{ background: 'rgba(0,212,170,0.07)', border: '1px solid rgba(0,212,170,0.2)' }}>
                  <MessageSquare size={11} className="mt-0.5 shrink-0" style={{ color: 'var(--color-teal)' }} />
                  <p className="text-xs" style={{ color: 'var(--color-teal)' }}>
                    <span className="font-semibold">Nota anterior: </span>{turno.notas_cliente}
                  </p>
                </div>
              )}

              {/* Notas post servicio */}
              {turno.notas_post_servicio && (
                <div className="mt-1.5 flex items-start gap-1.5 px-2.5 py-1.5 rounded-lg"
                  style={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)' }}>
                  <FileText size={11} className="mt-0.5 shrink-0" style={{ color: 'var(--color-text-3)' }} />
                  <p className="text-xs" style={{ color: 'var(--color-text-2)' }}>{turno.notas_post_servicio}</p>
                </div>
              )}
            </div>

            {/* Acciones */}
            <div className="flex flex-col gap-1.5 shrink-0">
              {canConfirm && (
                <button onClick={() => onAction(turno.id, 'confirmar')}
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: 'var(--color-success-bg)', color: 'var(--color-success)' }} title="Confirmar">
                  <Check size={14} />
                </button>
              )}
              {canAtender && (
                <button onClick={() => onAction(turno.id, 'atender')}
                  className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs"
                  style={{ background: 'rgba(0,212,170,0.1)', color: 'var(--color-teal)', border: '1px solid rgba(0,212,170,0.3)' }}
                  title="Marcar atendido">✓✓</button>
              )}
              {esAtendido && !turno.notas_post_servicio && (
                <button onClick={() => onNota(turno.id)}
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: '#eff6ff', color: '#3b82f6' }} title="Agregar nota">
                  <FileText size={14} />
                </button>
              )}
              {canAusente && (
                <button onClick={() => onAction(turno.id, 'ausente')}
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: 'var(--color-danger-bg)', color: 'var(--color-danger)' }} title="No vino">
                  <UserX size={14} />
                </button>
              )}
              {!esAtendido && (
                <button onClick={() => setMoodAbierto(!moodAbierto)}
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: moodSeleccionado ? `${moodCfg?.color}20` : 'var(--color-bg)', color: moodSeleccionado ? moodCfg?.color : 'var(--color-text-3)', border: '1px solid var(--color-border)' }}
                  title="Estado de ánimo">
                  <Smile size={14} />
                </button>
              )}
              {canCancelar && (
                <button onClick={() => onAction(turno.id, 'cancelar')}
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: 'var(--color-surface-2)', color: 'var(--color-text-3)' }} title="Cancelar">
                  <X size={14} />
                </button>
              )}
              <button onClick={() => setExpandido(!expandido)}
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: 'var(--color-bg)', color: 'var(--color-text-3)', border: '1px solid var(--color-border)' }}
                title="Ver ficha">
                {expandido ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
            </div>
          </div>

          {/* Selector de mood */}
          <AnimatePresence>
            {moodAbierto && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                className="mt-3 flex gap-2 flex-wrap overflow-hidden">
                {MOODS.map(m => (
                  <button key={m.id} onClick={() => { setMoodSeleccionado(m.id); setMoodAbierto(false) }}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium"
                    style={{ background: moodSeleccionado === m.id ? `${m.color}20` : 'var(--color-bg)', color: m.color, border: `1px solid ${m.color}40` }}>
                    <m.icon size={12} /> {m.label}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Ficha expandida (briefing completo) */}
          <AnimatePresence>
            {expandido && cliente && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                className="mt-3 overflow-hidden">
                <div className="rounded-xl p-4 space-y-3" style={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)' }}>
                  <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--color-text-3)' }}>
                    Briefing del cliente
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    {cliente.telefono && (
                      <a href={`tel:${cliente.telefono}`}
                        className="flex items-center gap-2 text-xs font-medium px-3 py-2 rounded-lg"
                        style={{ background: 'var(--color-surface)', color: 'var(--color-text-2)', border: '1px solid var(--color-border)' }}>
                        <Phone size={12} style={{ color: 'var(--color-teal)' }} />
                        {cliente.telefono}
                      </a>
                    )}
                    <div className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg"
                      style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                      <Clock size={12} style={{ color: 'var(--color-text-3)' }} />
                      <span style={{ color: 'var(--color-text-2)' }}>
                        Última visita: {cliente.ultima_visita ? format(new Date(cliente.ultima_visita), 'dd/MM/yy') : 'Primera vez'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg"
                      style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                      <Star size={12} style={{ color: '#f59e0b' }} />
                      <span style={{ color: 'var(--color-text-2)' }}>
                        Total gastado: ${(cliente.total_gastado || 0).toLocaleString('es-AR')}
                      </span>
                    </div>
                    {(cliente.ausencias || 0) > 0 && (
                      <div className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg"
                        style={{ background: '#fef2f2', border: '1px solid #fca5a5' }}>
                        <AlertTriangle size={12} style={{ color: '#ef4444' }} />
                        <span style={{ color: '#ef4444' }}>{cliente.ausencias} ausencias previas</span>
                      </div>
                    )}
                  </div>
                  {(cliente.alergias || cliente.tipo_piel || cliente.tipo_cabello) && (
                    <div className="pt-2" style={{ borderTop: '1px solid var(--color-border)' }}>
                      <p className="text-xs font-medium mb-1.5" style={{ color: 'var(--color-text-3)' }}>Datos relevantes</p>
                      <div className="flex gap-2 flex-wrap">
                        {cliente.alergias && (
                          <span className="text-xs px-2 py-1 rounded-lg font-medium"
                            style={{ background: '#fef2f2', color: '#ef4444', border: '1px solid #fca5a5' }}>
                            ⚠️ Alergia: {cliente.alergias}
                          </span>
                        )}
                        {cliente.tipo_piel && (
                          <span className="text-xs px-2 py-1 rounded-lg" style={{ background: 'var(--color-surface)', color: 'var(--color-text-2)', border: '1px solid var(--color-border)' }}>
                            Piel: {cliente.tipo_piel}
                          </span>
                        )}
                        {cliente.tipo_cabello && (
                          <span className="text-xs px-2 py-1 rounded-lg" style={{ background: 'var(--color-surface)', color: 'var(--color-text-2)', border: '1px solid var(--color-border)' }}>
                            Cabello: {cliente.tipo_cabello}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  {cliente.observaciones_internas && (
                    <div className="flex items-start gap-2 px-3 py-2 rounded-lg"
                      style={{ background: 'rgba(0,212,170,0.05)', border: '1px solid rgba(0,212,170,0.15)' }}>
                      <Info size={12} className="mt-0.5 shrink-0" style={{ color: 'var(--color-teal)' }} />
                      <p className="text-xs" style={{ color: 'var(--color-text-2)' }}>{cliente.observaciones_internas}</p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  )
}

// ─── Agenda principal ─────────────────────────────────────────────────────────
function Agenda() {
  const [fecha, setFecha] = useState(new Date())
  const [filtroTrabajador, setFiltroTrabajador] = useState<string>('todos')
  const [turnoNota, setTurnoNota] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const fechaStr   = format(fecha, 'yyyy-MM-dd')
  const fechaLabel = isToday(fecha) ? 'Hoy' : format(fecha, "EEEE d 'de' MMMM", { locale: es })

  const { data: trabajadores } = useQuery<Trabajador[]>({
    queryKey: ['trabajadores'],
    queryFn: () => trabajadoresApi.listar().then(r => r.data),
  })
  const trabajadorMap = Object.fromEntries((trabajadores || []).map(t => [t.id, t]))

  const { data: turnosData, isLoading } = useQuery<{ items: Turno[] }>({
    queryKey: ['turnos-agenda', fechaStr, filtroTrabajador],
    queryFn: () => turnosApi.listar({
      fecha: fechaStr, por_pagina: 100,
      ...(filtroTrabajador !== 'todos' ? { trabajador_id: filtroTrabajador } : {}),
    }).then(r => r.data),
    refetchInterval: 30000,
  })

  // Pre-cargar datos de clientes para los turnos del día
  const clienteIds = [...new Set((turnosData?.items || []).map(t => t.cliente_id))]
  const clientesQueries = useQuery<Record<string, Cliente>>({
    queryKey: ['clientes-agenda', clienteIds.join(',')],
    queryFn: async () => {
      if (!clienteIds.length) return {}
      const results = await Promise.all(clienteIds.map(id => clientesApi.obtener(id).then(r => r.data)))
      return Object.fromEntries(results.map(c => [c.id, c]))
    },
    enabled: clienteIds.length > 0,
  })
  const clienteMap = clientesQueries.data || {}

  const accion = useMutation({
    mutationFn: ({ id, tipo }: { id: string; tipo: string }) => {
      if (tipo === 'confirmar') return turnosApi.confirmar(id)
      if (tipo === 'atender')  return turnosApi.atender(id)
      if (tipo === 'ausente')  return turnosApi.ausente(id)
      if (tipo === 'cancelar') return turnosApi.cancelar(id)
      return Promise.reject()
    },
    onSuccess: (_, { tipo, id }) => {
      queryClient.invalidateQueries({ queryKey: ['turnos-agenda'] })
      queryClient.invalidateQueries({ queryKey: ['resumen'] })
      if (tipo === 'atender') setTurnoNota(id)
    },
  })

  const guardarNota = useMutation({
    mutationFn: ({ id, nota }: { id: string; nota: string }) => turnosApi.notas(id, nota),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['turnos-agenda'] }); setTurnoNota(null) },
  })

  const turnos      = turnosData?.items || []
  const pendientes  = turnos.filter(t => ['pendiente', 'confirmado', 'en_curso'].includes(t.estado))
  const finalizados = turnos.filter(t => ['atendido', 'cancelado', 'ausente'].includes(t.estado))
  const atendidos   = turnos.filter(t => t.estado === 'atendido')
  const sinConfirmar = turnos.filter(t => t.estado === 'pendiente').length
  const vipsHoy     = pendientes.filter(t => clienteMap[t.cliente_id]?.nivel_fidelizacion === 'vip').length
  const primeraVisitaHoy = pendientes.filter(t => (clienteMap[t.cliente_id]?.total_visitas || 0) <= 1).length
  const totalFacturado = atendidos.reduce((s, t) => s + (t.precio_base || 0), 0)
  const ocupacion   = turnos.length > 0 ? Math.round(atendidos.length / turnos.length * 100) : 0

  return (
    <div className="p-8 max-w-4xl mx-auto">

      <AnimatePresence>
        {turnoNota && (
          <NotasModal
            onClose={() => setTurnoNota(null)}
            onSave={nota => guardarNota.mutate({ id: turnoNota, nota })}
            onAgendarSiguiente={() => { setTurnoNota(null) }}
          />
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>Agenda</h1>
          <p className="text-sm mt-0.5 capitalize" style={{ color: 'var(--color-text-3)' }}>{fechaLabel}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setFecha(subDays(fecha, 1))} className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-2)' }}>
            <ChevronLeft size={18} />
          </button>
          <button onClick={() => setFecha(new Date())} className="px-4 h-9 rounded-xl text-sm font-medium"
            style={{ background: isToday(fecha) ? 'var(--color-teal)' : 'var(--color-surface)', color: isToday(fecha) ? 'var(--color-navy)' : 'var(--color-text-2)', border: '1px solid var(--color-border)' }}>
            Hoy
          </button>
          <button onClick={() => setFecha(addDays(fecha, 1))} className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-2)' }}>
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      {/* Alertas inteligentes del día */}
      {(sinConfirmar > 0 || vipsHoy > 0 || primeraVisitaHoy > 0) && (
        <div className="mb-5 space-y-2">
          {sinConfirmar > 0 && (
            <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm"
              style={{ background: '#fffbeb', border: '1px solid #fcd34d' }}>
              <AlertCircle size={16} style={{ color: '#f59e0b' }} />
              <span style={{ color: '#92400e' }}>
                <strong>{sinConfirmar} {sinConfirmar === 1 ? 'turno' : 'turnos'}</strong> pendiente{sinConfirmar > 1 ? 's' : ''} de confirmación
              </span>
            </motion.div>
          )}
          {vipsHoy > 0 && (
            <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
              className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm"
              style={{ background: '#fffbeb', border: '1px solid #fcd34d' }}>
              <Crown size={16} style={{ color: '#f59e0b' }} />
              <span style={{ color: '#92400e' }}>
                Hoy vienen <strong>{vipsHoy} cliente{vipsHoy > 1 ? 's' : ''} VIP</strong> — dale prioridad
              </span>
            </motion.div>
          )}
          {primeraVisitaHoy > 0 && (
            <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
              className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm"
              style={{ background: '#ecfdf5', border: '1px solid #6ee7b7' }}>
              <Sparkles size={16} style={{ color: '#10b981' }} />
              <span style={{ color: '#065f46' }}>
                <strong>{primeraVisitaHoy} cliente{primeraVisitaHoy > 1 ? 's' : ''} nuevo{primeraVisitaHoy > 1 ? 's' : ''}</strong> hoy — primera impresión cuenta
              </span>
            </motion.div>
          )}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3 mb-4">
        {[
          { label: 'Total', value: turnos.length, color: 'var(--color-text-2)' },
          { label: 'Activos', value: pendientes.length, color: '#f59e0b' },
          { label: 'Atendidos', value: atendidos.length, color: 'var(--color-teal)' },
          { label: 'Facturado', value: `$${totalFacturado.toLocaleString('es-AR')}`, color: 'var(--color-teal)' },
        ].map(s => (
          <div key={s.label} className="rounded-xl p-3 text-center"
            style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
            <p className="text-xl font-bold" style={{ fontFamily: 'var(--font-display)', color: s.color }}>{s.value}</p>
            <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>{s.label}</p>
          </div>
        ))}
      </div>

      {/* Barra de progreso del día */}
      {turnos.length > 0 && (
        <div className="mb-5 rounded-xl p-4" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium" style={{ color: 'var(--color-text-2)' }}>Progreso del día</span>
            <span className="text-xs font-bold" style={{ color: 'var(--color-teal)' }}>{ocupacion}% completado</span>
          </div>
          <div className="h-2 rounded-full overflow-hidden" style={{ background: 'var(--color-bg)' }}>
            <motion.div className="h-full rounded-full" style={{ background: 'var(--color-teal)' }}
              initial={{ width: 0 }} animate={{ width: `${ocupacion}%` }} transition={{ duration: 0.8 }} />
          </div>
        </div>
      )}

      {/* Filtro trabajadores */}
      {trabajadores && trabajadores.length > 1 && (
        <div className="flex gap-2 mb-5 flex-wrap">
          <button onClick={() => setFiltroTrabajador('todos')}
            className="px-3 py-1.5 rounded-lg text-xs font-medium"
            style={{ background: filtroTrabajador === 'todos' ? 'var(--color-navy)' : 'var(--color-surface)', color: filtroTrabajador === 'todos' ? 'var(--color-teal)' : 'var(--color-text-2)', border: '1px solid var(--color-border)' }}>
            Todos
          </button>
          {trabajadores.map(t => (
            <button key={t.id} onClick={() => setFiltroTrabajador(t.id)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5"
              style={{ background: filtroTrabajador === t.id ? `${t.color_agenda}20` : 'var(--color-surface)', color: filtroTrabajador === t.id ? t.color_agenda : 'var(--color-text-2)', border: `1px solid ${filtroTrabajador === t.id ? t.color_agenda : 'var(--color-border)'}` }}>
              <div className="w-2 h-2 rounded-full" style={{ background: t.color_agenda }} />
              {t.nombre}
            </button>
          ))}
        </div>
      )}

      {/* Lista */}
      {isLoading ? (
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="h-24 rounded-2xl animate-pulse" style={{ background: 'var(--color-border)' }} />)}
        </div>
      ) : turnos.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
            style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
            <Clock size={28} style={{ color: 'var(--color-text-3)' }} />
          </div>
          <p className="font-semibold" style={{ color: 'var(--color-text-2)' }}>Sin turnos para este día</p>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-3)' }}>Los turnos reservados aparecerán acá</p>
        </div>
      ) : (
        <div>
          {pendientes.length > 0 && (
            <div className="mb-6">
              <p className="text-xs font-semibold uppercase tracking-widest mb-3 flex items-center gap-2" style={{ color: 'var(--color-text-3)' }}>
                <AlertCircle size={12} /> Activos · {pendientes.length}
              </p>
              {pendientes.sort((a,b) => a.hora_inicio.localeCompare(b.hora_inicio)).map(t => (
                <TurnoCard key={t.id} turno={t}
                  trabajadorColor={trabajadorMap[t.trabajador_id]?.color_agenda || 'var(--color-teal)'}
                  cliente={clienteMap[t.cliente_id]}
                  onAction={(id, tipo) => accion.mutate({ id, tipo })}
                  onNota={id => setTurnoNota(id)} />
              ))}
            </div>
          )}
          {finalizados.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--color-text-3)' }}>
                Finalizados · {finalizados.length}
              </p>
              {finalizados.sort((a,b) => a.hora_inicio.localeCompare(b.hora_inicio)).map(t => (
                <TurnoCard key={t.id} turno={t}
                  trabajadorColor={trabajadorMap[t.trabajador_id]?.color_agenda || '#94a3b8'}
                  cliente={clienteMap[t.cliente_id]}
                  onAction={(id, tipo) => accion.mutate({ id, tipo })}
                  onNota={id => setTurnoNota(id)} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}