'use client'
 
import { useQuery } from '@tanstack/react-query'
import { useParams, useRouter } from 'next/navigation'
import { clientesApi, turnosApi } from '@/lib/api'
import { Cliente, Turno } from '@/types'
import { motion } from 'framer-motion'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import {
  ArrowLeft, Crown, Star, Sparkles, Flame, Phone, Mail,
  Calendar, MapPin, Gift, Heart, Cake, MessageCircle,
  TrendingUp, Clock, Scissors, CheckCircle2, XCircle,
  AlertTriangle, FileText, Briefcase, CreditCard
} from 'lucide-react'
 
const qc = new QueryClient()
export default function ClientePerfilPage() {
  return <QueryClientProvider client={qc}><Perfil /></QueryClientProvider>
}
 
const NIVEL: Record<string, { icon: React.ElementType; label: string; color: string; bg: string }> = {
  vip:       { icon: Crown,    label: 'VIP',       color: '#f59e0b', bg: '#fffbeb' },
  frecuente: { icon: Flame,    label: 'Frecuente', color: '#8b5cf6', bg: '#f5f3ff' },
  regular:   { icon: Star,     label: 'Regular',   color: '#3b82f6', bg: '#eff6ff' },
  nuevo:     { icon: Sparkles, label: 'Nuevo',     color: '#10b981', bg: '#ecfdf5' },
}
 
const ESTADO_TURNO: Record<string, { label: string; color: string; bg: string; icon: React.ElementType }> = {
  atendido:   { label: 'Atendido',   color: '#3b82f6', bg: '#eff6ff', icon: CheckCircle2 },
  confirmado: { label: 'Confirmado', color: '#10b981', bg: '#ecfdf5', icon: CheckCircle2 },
  pendiente:  { label: 'Pendiente',  color: '#f59e0b', bg: '#fffbeb', icon: Clock },
  cancelado:  { label: 'Cancelado',  color: '#94a3b8', bg: '#f8fafc', icon: XCircle },
  ausente:    { label: 'Ausente',    color: '#ef4444', bg: '#fef2f2', icon: XCircle },
}
 
function DatoItem({ icon: Icon, label, valor, color = 'var(--color-text-3)' }: {
  icon: React.ElementType; label: string; valor?: string | null; color?: string
}) {
  if (!valor) return null
  return (
    <div className="flex items-center gap-3 py-2">
      <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ background: 'var(--color-bg)' }}>
        <Icon size={14} style={{ color }} />
      </div>
      <div className="min-w-0">
        <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>{label}</p>
        <p className="text-sm font-medium truncate" style={{ color: 'var(--color-text-1)' }}>{valor}</p>
      </div>
    </div>
  )
}
 
function Perfil() {
  const params = useParams()
  const router = useRouter()
  const clienteId = params.id as string
 
  const { data: c, isLoading } = useQuery<Cliente>({
    queryKey: ['cliente', clienteId],
    queryFn: () => clientesApi.obtener(clienteId).then(r => r.data),
  })
 
  const { data: turnosData } = useQuery<{ items: Turno[] }>({
    queryKey: ['cliente-turnos', clienteId],
    queryFn: () => turnosApi.listar({ cliente_id: clienteId, por_pagina: 100 }).then(r => r.data),
    enabled: !!clienteId,
  })
 
  const turnos = (turnosData?.items || []).sort((a, b) =>
    `${b.fecha}${b.hora_inicio}`.localeCompare(`${a.fecha}${a.hora_inicio}`))
 
  if (isLoading || !c) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="h-40 rounded-3xl animate-pulse mb-4" style={{ background: 'var(--color-border)' }} />
        <div className="h-64 rounded-2xl animate-pulse" style={{ background: 'var(--color-border)' }} />
      </div>
    )
  }
 
  const nivel = NIVEL[c.nivel_fidelizacion] || NIVEL.nuevo
  const edad = c.fecha_nacimiento ? Math.floor((Date.now() - new Date(c.fecha_nacimiento).getTime()) / 31557600000) : null
  const cumpleHoy = c.fecha_nacimiento && (() => {
    const d = new Date(c.fecha_nacimiento); const h = new Date()
    return d.getDate() === h.getDate() && d.getMonth() === h.getMonth()
  })()
 
  return (
    <div className="p-8 max-w-4xl mx-auto">
 
      {/* Volver */}
      <button onClick={() => router.push('/clientes')} className="flex items-center gap-2 text-sm font-medium mb-4" style={{ color: 'var(--color-text-3)' }}>
        <ArrowLeft size={16} /> Volver a clientes
      </button>
 
      {/* Header del perfil */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
        className="rounded-3xl p-6 mb-6" style={{ background: 'var(--color-navy)' }}>
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-3xl flex items-center justify-center text-2xl font-bold shrink-0"
            style={{ background: `${nivel.color}25`, color: nivel.color, border: `2px solid ${nivel.color}`, fontFamily: 'var(--font-display)' }}>
            {c.nombre.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'var(--font-display)' }}>
                {c.nombre} {c.apellido || ''}
              </h1>
              <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium"
                style={{ background: `${nivel.color}25`, color: nivel.color }}>
                <nivel.icon size={11} /> {nivel.label}
              </span>
              {cumpleHoy && (
                <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium" style={{ background: '#a855f725', color: '#d8b4fe' }}>
                  <Cake size={11} /> ¡Cumple hoy!
                </span>
              )}
            </div>
            <div className="flex items-center gap-4 flex-wrap text-sm" style={{ color: 'rgba(255,255,255,0.6)' }}>
              {c.telefono && <span className="flex items-center gap-1"><Phone size={12} /> {c.telefono}</span>}
              {c.email && <span className="flex items-center gap-1"><Mail size={12} /> {c.email}</span>}
              {edad && <span>{edad} años</span>}
            </div>
            {c.telefono && (
              <div className="flex gap-2 mt-3">
                <a href={`https://wa.me/${c.telefono.replace(/\D/g, '')}`} target="_blank" rel="noreferrer"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium" style={{ background: '#16a34a', color: 'white' }}>
                  <MessageCircle size={13} /> WhatsApp
                </a>
                <a href={`tel:${c.telefono}`} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium"
                  style={{ background: 'rgba(255,255,255,0.1)', color: 'white' }}>
                  <Phone size={13} /> Llamar
                </a>
              </div>
            )}
          </div>
        </div>
 
        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mt-5">
          <div className="rounded-2xl p-3 text-center" style={{ background: 'rgba(255,255,255,0.05)' }}>
            <p className="text-xl font-bold text-white" style={{ fontFamily: 'var(--font-display)' }}>{c.total_visitas}</p>
            <p className="text-xs" style={{ color: 'rgba(255,255,255,0.5)' }}>visitas</p>
          </div>
          <div className="rounded-2xl p-3 text-center" style={{ background: 'rgba(255,255,255,0.05)' }}>
            <p className="text-xl font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-teal)' }}>${(c.total_gastado || 0).toLocaleString('es-AR')}</p>
            <p className="text-xs" style={{ color: 'rgba(255,255,255,0.5)' }}>gastado</p>
          </div>
          <div className="rounded-2xl p-3 text-center" style={{ background: 'rgba(255,255,255,0.05)' }}>
            <p className="text-xl font-bold" style={{ fontFamily: 'var(--font-display)', color: (c.ausencias || 0) > 0 ? '#fca5a5' : 'white' }}>{c.ausencias || 0}</p>
            <p className="text-xs" style={{ color: 'rgba(255,255,255,0.5)' }}>ausencias</p>
          </div>
        </div>
      </motion.div>
 
      {/* Alerta de alergias */}
      {c.alergias && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl mb-6" style={{ background: '#fef2f2', border: '1px solid #fca5a5' }}>
          <AlertTriangle size={18} style={{ color: '#ef4444' }} />
          <div>
            <p className="text-sm font-semibold" style={{ color: '#ef4444' }}>Alergias</p>
            <p className="text-sm" style={{ color: '#b91c1c' }}>{c.alergias}</p>
          </div>
        </div>
      )}
 
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
 
        {/* Datos del cliente */}
        <div className="rounded-2xl p-5" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <h3 className="font-semibold text-sm mb-3" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>Datos</h3>
          <div className="divide-y" style={{ borderColor: 'var(--color-border)' }}>
            <DatoItem icon={CreditCard} label="DNI" valor={c.dni} />
            <DatoItem icon={Cake} label="Nacimiento" valor={c.fecha_nacimiento ? format(new Date(c.fecha_nacimiento), "d 'de' MMMM yyyy", { locale: es }) : null} color="#a855f7" />
            <DatoItem icon={Heart} label="Aniversario" valor={c.fecha_aniversario ? format(new Date(c.fecha_aniversario), "d 'de' MMMM", { locale: es }) : null} color="#ec4899" />
            <DatoItem icon={MapPin} label="Dirección" valor={c.direccion} />
            <DatoItem icon={Briefcase} label="Ocupación" valor={c.ocupacion} />
            <DatoItem icon={Scissors} label="Tipo de cabello" valor={c.tipo_cabello} />
            <DatoItem icon={Sparkles} label="Tipo de piel" valor={c.tipo_piel} />
          </div>
          {c.observaciones_internas && (
            <div className="mt-3 flex items-start gap-2 px-3 py-2 rounded-xl" style={{ background: 'rgba(0,212,170,0.05)', border: '1px solid rgba(0,212,170,0.15)' }}>
              <FileText size={13} className="mt-0.5 shrink-0" style={{ color: 'var(--color-teal)' }} />
              <p className="text-xs" style={{ color: 'var(--color-text-2)' }}>{c.observaciones_internas}</p>
            </div>
          )}
          {/* Consentimientos */}
          <div className="mt-3 flex gap-2 flex-wrap">
            {c.acepta_recordatorios && <span className="text-xs px-2 py-1 rounded-lg" style={{ background: '#eff6ff', color: '#3b82f6' }}>✓ Recordatorios</span>}
            {c.acepta_promociones && <span className="text-xs px-2 py-1 rounded-lg" style={{ background: '#fffbeb', color: '#f59e0b' }}>✓ Promociones</span>}
            {c.acepta_cumpleanos && <span className="text-xs px-2 py-1 rounded-lg" style={{ background: '#fdf4ff', color: '#a855f7' }}>✓ Cumpleaños</span>}
          </div>
        </div>
 
        {/* Historial de turnos */}
        <div className="rounded-2xl p-5" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <h3 className="font-semibold text-sm mb-3" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
            Historial · {turnos.length} turnos
          </h3>
          {turnos.length === 0 ? (
            <div className="flex flex-col items-center py-10">
              <Clock size={28} className="mb-2" style={{ color: 'var(--color-text-3)' }} />
              <p className="text-sm" style={{ color: 'var(--color-text-3)' }}>Sin turnos todavía</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto relative">
              {turnos.map((t) => {
                const est = ESTADO_TURNO[t.estado] || ESTADO_TURNO.pendiente
                return (
                  <div key={t.id} className="flex items-center gap-3 p-3 rounded-xl" style={{ background: 'var(--color-bg)' }}>
                    <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ background: est.bg }}>
                      <est.icon size={15} style={{ color: est.color }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate" style={{ color: 'var(--color-text-1)' }}>{t.servicio_nombre}</p>
                      <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>
                        {format(new Date(t.fecha + 'T12:00:00'), "d MMM yyyy", { locale: es })} · {t.trabajador_nombre}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-xs px-2 py-0.5 rounded-full font-medium" style={{ background: est.bg, color: est.color }}>{est.label}</span>
                      {t.precio_base && <p className="text-xs font-semibold mt-0.5" style={{ color: 'var(--color-teal)' }}>${t.precio_base.toLocaleString('es-AR')}</p>}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}