'use client'
 
import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { clientesApi } from '@/lib/api'
import { Cliente } from '@/types'
import { motion } from 'framer-motion'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ClienteFormModal from '@/components/cliente/ClienteFormModal'
import {
  Search, Crown, Star, Sparkles, Phone, Calendar,
  TrendingUp, ChevronRight, AlertTriangle, MessageCircle,
  CalendarPlus, LayoutGrid, List, Flame, UserPlus, X
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'
 
const qc = new QueryClient()
export default function ClientesPage() {
  return <QueryClientProvider client={qc}><Clientes /></QueryClientProvider>
}
 
const NIVEL: Record<string, { icon: React.ElementType; label: string; color: string; bg: string; ring: string }> = {
  vip:       { icon: Crown,    label: 'VIP',       color: '#f59e0b', bg: '#fffbeb', ring: '#fcd34d' },
  frecuente: { icon: Flame,    label: 'Frecuente', color: '#8b5cf6', bg: '#f5f3ff', ring: '#c4b5fd' },
  regular:   { icon: Star,     label: 'Regular',   color: '#3b82f6', bg: '#eff6ff', ring: '#93c5fd' },
  nuevo:     { icon: Sparkles, label: 'Nuevo',     color: '#10b981', bg: '#ecfdf5', ring: '#6ee7b7' },
}
 
function calcularSalud(c: Cliente): { score: number; label: string; color: string } {
  const dias = c.ultima_visita ? Math.floor((Date.now() - new Date(c.ultima_visita).getTime()) / 86400000) : 999
  if (!c.ultima_visita || dias > 90)   return { score: 10, label: 'Perdido',   color: '#ef4444' }
  if (dias > 45)                       return { score: 35, label: 'En riesgo', color: '#f97316' }
  if (dias > 21)                       return { score: 60, label: 'Tibiando',  color: '#f59e0b' }
  if (c.nivel_fidelizacion === 'vip')  return { score: 98, label: 'Embajador', color: '#10b981' }
  if (c.nivel_fidelizacion === 'frecuente') return { score: 85, label: 'Leal', color: '#10b981' }
  return { score: 72, label: 'Activo', color: '#3b82f6' }
}
 
function ActividadBar({ visitas, nivel }: { visitas: number; nivel: string }) {
  const cfg = NIVEL[nivel] || NIVEL.nuevo
  const barras = Math.min(visitas, 8)
  return (
    <div className="flex items-end gap-0.5" style={{ height: '18px' }}>
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="w-1.5 rounded-sm" style={{
          height: `${i < barras ? 8 + (i % 3) * 4 : 4}px`,
          background: i < barras ? cfg.color : 'var(--color-border)',
          opacity: i < barras ? 0.7 + (i / barras) * 0.3 : 1,
        }} />
      ))}
    </div>
  )
}
 
function ClienteCardGrid({ c, onClick }: { c: Cliente; onClick: () => void }) {
  const cfg = NIVEL[c.nivel_fidelizacion] || NIVEL.nuevo
  const salud = calcularSalud(c)
  const diasStr = c.ultima_visita ? formatDistanceToNow(new Date(c.ultima_visita), { locale: es, addSuffix: true }) : 'Sin visitas'
 
  return (
    <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
      onClick={onClick}
      className="rounded-2xl p-5 flex flex-col gap-3 group cursor-pointer relative overflow-hidden"
      style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
      <div className="absolute top-0 left-0 right-0 h-0.5"
        style={{ background: `linear-gradient(90deg, ${salud.color} ${salud.score}%, var(--color-border) ${salud.score}%)` }} />
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl flex items-center justify-center text-base font-bold shrink-0"
            style={{ background: `${cfg.color}18`, color: cfg.color, border: `1.5px solid ${cfg.ring}`, fontFamily: 'var(--font-display)' }}>
            {c.nombre.charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="font-semibold text-sm leading-tight" style={{ color: 'var(--color-text-1)' }}>
              {c.nombre} {c.apellido || ''}
            </p>
            <span className="flex items-center gap-1 text-xs font-medium mt-0.5" style={{ color: cfg.color }}>
              <cfg.icon size={10} /> {cfg.label}
            </span>
          </div>
        </div>
        <span className="text-xs px-2 py-0.5 rounded-full font-medium" style={{ background: `${salud.color}15`, color: salud.color }}>
          {salud.label}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-xl p-2.5" style={{ background: 'var(--color-bg)' }}>
          <p className="text-base font-bold leading-none mb-0.5" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>{c.total_visitas}</p>
          <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>visitas</p>
        </div>
        <div className="rounded-xl p-2.5" style={{ background: 'var(--color-bg)' }}>
          <p className="text-base font-bold leading-none mb-0.5" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-teal)' }}>${((c.total_gastado || 0) / 1000).toFixed(0)}k</p>
          <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>gastado</p>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <ActividadBar visitas={c.total_visitas} nivel={c.nivel_fidelizacion} />
        <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>{diasStr}</p>
      </div>
      <div className="flex gap-1.5 flex-wrap">
        {c.telefono && (
          <a href={`tel:${c.telefono}`} onClick={e => e.stopPropagation()}
            className="flex items-center gap-1 text-xs px-2 py-1 rounded-lg font-medium"
            style={{ background: 'rgba(0,212,170,0.08)', color: 'var(--color-teal)', border: '1px solid rgba(0,212,170,0.2)' }}>
            <Phone size={10} /> {c.telefono}
          </a>
        )}
        {c.alergias && (
          <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-lg" style={{ background: '#fef2f2', color: '#ef4444', border: '1px solid #fca5a5' }}>
            ⚠️ {c.alergias}
          </span>
        )}
      </div>
      <div className="flex gap-2 pt-1" style={{ borderTop: '1px solid var(--color-border)' }}>
        {c.telefono && (
          <a href={`https://wa.me/${c.telefono.replace(/\D/g, '')}`} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-medium"
            style={{ background: '#dcfce7', color: '#16a34a' }}>
            <MessageCircle size={12} /> WhatsApp
          </a>
        )}
        <button onClick={e => { e.stopPropagation(); onClick() }} className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-medium"
          style={{ background: 'rgba(0,212,170,0.1)', color: 'var(--color-teal)', border: '1px solid rgba(0,212,170,0.2)' }}>
          Ver ficha <ChevronRight size={12} />
        </button>
      </div>
    </motion.div>
  )
}
 
function ClienteRow({ c, onClick }: { c: Cliente; onClick: () => void }) {
  const cfg = NIVEL[c.nivel_fidelizacion] || NIVEL.nuevo
  const salud = calcularSalud(c)
  const dias = c.ultima_visita ? Math.floor((Date.now() - new Date(c.ultima_visita).getTime()) / 86400000) : null
  return (
    <motion.div initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} onClick={onClick}
      className="flex items-center gap-4 px-4 py-3 cursor-pointer">
      <div className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm shrink-0"
        style={{ background: `${cfg.color}15`, color: cfg.color, fontFamily: 'var(--font-display)' }}>
        {c.nombre.charAt(0)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-semibold truncate" style={{ color: 'var(--color-text-1)' }}>{c.nombre} {c.apellido || ''}</p>
          <span className="text-xs px-1.5 py-0.5 rounded-md font-medium shrink-0" style={{ background: cfg.bg, color: cfg.color }}>{cfg.label}</span>
        </div>
        <p className="text-xs truncate" style={{ color: 'var(--color-text-3)' }}>{c.telefono || c.email || 'Sin contacto'}</p>
      </div>
      <div className="text-center shrink-0 w-16 hidden sm:block">
        <p className="text-sm font-bold" style={{ color: 'var(--color-text-1)' }}>{c.total_visitas}</p>
        <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>visitas</p>
      </div>
      <div className="text-center shrink-0 w-20 hidden md:block">
        <p className="text-sm font-bold" style={{ color: 'var(--color-teal)' }}>${((c.total_gastado || 0) / 1000).toFixed(1)}k</p>
        <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>gastado</p>
      </div>
      <div className="text-right shrink-0 hidden lg:block">
        <p className="text-xs font-medium" style={{ color: salud.color }}>{salud.label}</p>
        <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>{dias !== null ? (dias === 0 ? 'Hoy' : `Hace ${dias}d`) : '—'}</p>
      </div>
      <ChevronRight size={14} className="shrink-0" style={{ color: 'var(--color-text-3)' }} />
    </motion.div>
  )
}
 
function SegmentoChip({ label, count, active, color, onClick }: { label: string; count: number; active: boolean; color: string; onClick: () => void }) {
  return (
    <button onClick={onClick} className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold transition-all shrink-0"
      style={{ background: active ? `${color}18` : 'var(--color-surface)', color: active ? color : 'var(--color-text-2)', border: `1.5px solid ${active ? color : 'var(--color-border)'}` }}>
      {label}
      <span className="px-1.5 py-0.5 rounded-md text-xs font-bold" style={{ background: active ? `${color}25` : 'var(--color-bg)', color: active ? color : 'var(--color-text-3)' }}>{count}</span>
    </button>
  )
}
 
function Clientes() {
  const router = useRouter()
  const [busqueda, setBusqueda] = useState('')
  const [filtroNivel, setFiltroNivel] = useState('todos')
  const [vista, setVista] = useState<'grid' | 'lista'>('grid')
  const [ordenar, setOrdenar] = useState('ultima_visita')
  const [pagina, setPagina] = useState(1)
  const [modalAbierto, setModalAbierto] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
 
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); inputRef.current?.focus() }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])
 
  const { data, isLoading } = useQuery({
    queryKey: ['clientes', busqueda, filtroNivel, pagina, ordenar],
    queryFn: () => clientesApi.listar({ q: busqueda || undefined, nivel: filtroNivel !== 'todos' ? filtroNivel : undefined, pagina, por_pagina: 24 }).then(r => r.data),
    placeholderData: (prev: typeof data) => prev,
  })
  const clientes: Cliente[] = data?.items || []
  const total = data?.total || 0
 
  const { data: todos } = useQuery({
    queryKey: ['clientes-todos'],
    queryFn: () => clientesApi.listar({ por_pagina: 500 }).then(r => r.data),
    staleTime: 60000,
  })
  const allClientes: Cliente[] = todos?.items || []
  const conteos = {
    todos: allClientes.length,
    vip: allClientes.filter(c => c.nivel_fidelizacion === 'vip').length,
    frecuente: allClientes.filter(c => c.nivel_fidelizacion === 'frecuente').length,
    regular: allClientes.filter(c => c.nivel_fidelizacion === 'regular').length,
    nuevo: allClientes.filter(c => c.nivel_fidelizacion === 'nuevo').length,
    riesgo: allClientes.filter(c => {
      const d = c.ultima_visita ? Math.floor((Date.now() - new Date(c.ultima_visita).getTime()) / 86400000) : 999
      return d > 45 && c.total_visitas >= 3
    }).length,
  }
  const ltv = allClientes.length > 0 ? allClientes.reduce((s, c) => s + (c.total_gastado || 0), 0) / allClientes.length : 0
 
  const irAlPerfil = (id: string) => router.push(`/clientes/${id}`)
 
  return (
    <div className="p-8 max-w-6xl mx-auto">
      {modalAbierto && <ClienteFormModal onClose={() => setModalAbierto(false)} onCreado={(c) => irAlPerfil(c.id)} />}
 
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>Clientes</h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--color-text-3)' }}>
            {total} clientes · LTV promedio ${ltv.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
          </p>
        </div>
        <button onClick={() => setModalAbierto(true)} className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold"
          style={{ background: 'var(--color-teal)', color: 'var(--color-navy)', fontFamily: 'var(--font-display)' }}>
          <UserPlus size={16} /> Nuevo cliente
        </button>
      </div>
 
      <div className="grid grid-cols-4 gap-3 mb-6">
        {[
          { label: 'Total', value: conteos.todos, color: 'var(--color-text-1)' },
          { label: 'VIP 👑', value: conteos.vip, color: '#f59e0b' },
          { label: 'En riesgo', value: conteos.riesgo, color: '#ef4444' },
          { label: 'LTV prom.', value: `$${(ltv / 1000).toFixed(1)}k`, color: 'var(--color-teal)' },
        ].map(k => (
          <div key={k.label} className="rounded-2xl p-4" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
            <p className="text-2xl font-bold mb-0.5" style={{ fontFamily: 'var(--font-display)', color: k.color }}>{k.value}</p>
            <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>{k.label}</p>
          </div>
        ))}
      </div>
 
      <div className="flex gap-3 mb-4 items-center">
        <div className="flex-1 relative">
          <Search size={15} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-3)' }} />
          <input ref={inputRef} type="text" placeholder="Buscar cliente... (Ctrl+K)" value={busqueda}
            onChange={e => { setBusqueda(e.target.value); setPagina(1) }}
            className="w-full h-11 pl-10 pr-10 rounded-xl text-sm outline-none"
            style={{ background: 'var(--color-surface)', border: '1.5px solid var(--color-border)', color: 'var(--color-text-1)' }} />
          {busqueda && <button onClick={() => setBusqueda('')} className="absolute right-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-3)' }}><X size={14} /></button>}
        </div>
        <select value={ordenar} onChange={e => setOrdenar(e.target.value)} className="h-11 px-3 rounded-xl text-sm outline-none cursor-pointer"
          style={{ background: 'var(--color-surface)', border: '1.5px solid var(--color-border)', color: 'var(--color-text-2)' }}>
          <option value="ultima_visita">Última visita</option>
          <option value="total_gastado">Mayor gasto</option>
          <option value="total_visitas">Más visitas</option>
          <option value="nombre">Nombre A-Z</option>
        </select>
        <div className="flex rounded-xl overflow-hidden" style={{ border: '1.5px solid var(--color-border)' }}>
          <button onClick={() => setVista('grid')} className="w-10 h-11 flex items-center justify-center"
            style={{ background: vista === 'grid' ? 'var(--color-navy)' : 'var(--color-surface)', color: vista === 'grid' ? 'var(--color-teal)' : 'var(--color-text-3)' }}>
            <LayoutGrid size={15} />
          </button>
          <button onClick={() => setVista('lista')} className="w-10 h-11 flex items-center justify-center"
            style={{ background: vista === 'lista' ? 'var(--color-navy)' : 'var(--color-surface)', color: vista === 'lista' ? 'var(--color-teal)' : 'var(--color-text-3)' }}>
            <List size={15} />
          </button>
        </div>
      </div>
 
      <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
        <SegmentoChip label="Todos" count={conteos.todos} active={filtroNivel === 'todos'} color="var(--color-text-1)" onClick={() => { setFiltroNivel('todos'); setPagina(1) }} />
        <SegmentoChip label="👑 VIP" count={conteos.vip} active={filtroNivel === 'vip'} color="#f59e0b" onClick={() => { setFiltroNivel('vip'); setPagina(1) }} />
        <SegmentoChip label="🔥 Frecuentes" count={conteos.frecuente} active={filtroNivel === 'frecuente'} color="#8b5cf6" onClick={() => { setFiltroNivel('frecuente'); setPagina(1) }} />
        <SegmentoChip label="⭐ Regulares" count={conteos.regular} active={filtroNivel === 'regular'} color="#3b82f6" onClick={() => { setFiltroNivel('regular'); setPagina(1) }} />
        <SegmentoChip label="✨ Nuevos" count={conteos.nuevo} active={filtroNivel === 'nuevo'} color="#10b981" onClick={() => { setFiltroNivel('nuevo'); setPagina(1) }} />
        <SegmentoChip label="⚠️ En riesgo" count={conteos.riesgo} active={filtroNivel === 'riesgo'} color="#ef4444" onClick={() => { setFiltroNivel('riesgo'); setPagina(1) }} />
      </div>
 
      {isLoading ? (
        <div className={vista === 'grid' ? "grid grid-cols-2 xl:grid-cols-3 gap-4" : "space-y-2"}>
          {Array.from({ length: 6 }).map((_, i) => <div key={i} className="rounded-2xl animate-pulse" style={{ height: vista === 'grid' ? '220px' : '64px', background: 'var(--color-border)' }} />)}
        </div>
      ) : clientes.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 text-3xl" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>🔍</div>
          <p className="font-semibold" style={{ color: 'var(--color-text-2)' }}>{busqueda ? `Sin resultados para "${busqueda}"` : 'Sin clientes en este segmento'}</p>
        </div>
      ) : vista === 'grid' ? (
        <div className="grid grid-cols-2 xl:grid-cols-3 gap-4 stagger">
          {clientes.map(c => <ClienteCardGrid key={c.id} c={c} onClick={() => irAlPerfil(c.id)} />)}
        </div>
      ) : (
        <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          {clientes.map((c, i) => (
            <div key={c.id} style={{ borderBottom: i < clientes.length - 1 ? '1px solid var(--color-border)' : 'none' }}>
              <ClienteRow c={c} onClick={() => irAlPerfil(c.id)} />
            </div>
          ))}
        </div>
      )}
 
      {total > 24 && (
        <div className="flex items-center justify-between mt-6">
          <p className="text-sm" style={{ color: 'var(--color-text-3)' }}>{(pagina - 1) * 24 + 1}–{Math.min(pagina * 24, total)} de {total} clientes</p>
          <div className="flex gap-2">
            <button onClick={() => setPagina(p => Math.max(1, p - 1))} disabled={pagina === 1} className="px-4 py-2 rounded-xl text-sm font-medium disabled:opacity-40"
              style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-2)' }}>← Anterior</button>
            <button onClick={() => setPagina(p => p + 1)} disabled={pagina * 24 >= total} className="px-4 py-2 rounded-xl text-sm font-medium disabled:opacity-40"
              style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-2)' }}>Siguiente →</button>
          </div>
        </div>
      )}
    </div>
  )
}