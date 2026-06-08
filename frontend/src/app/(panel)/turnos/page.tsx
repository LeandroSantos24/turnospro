'use client'
 
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clientesApi, serviciosApi, trabajadoresApi, turnosApi } from '@/lib/api'
import { Cliente, Servicio, Trabajador } from '@/types'
import { motion, AnimatePresence } from 'framer-motion'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { format, addDays, isToday, isTomorrow } from 'date-fns'
import { es } from 'date-fns/locale'
import {
  Search, Plus, Check, User, Scissors, Clock, Calendar,
  ChevronRight, Crown, Star, Sparkles, X, CheckCircle2,
  Phone, UserPlus, CalendarCheck, Zap
} from 'lucide-react'
 
const qc = new QueryClient()
export default function NuevoTurnoPage() {
  return <QueryClientProvider client={qc}><NuevoTurno /></QueryClientProvider>
}
 
const NIVEL: Record<string, { icon: React.ElementType; color: string }> = {
  vip:       { icon: Crown,    color: '#f59e0b' },
  frecuente: { icon: Star,     color: '#8b5cf6' },
  regular:   { icon: Star,     color: '#3b82f6' },
  nuevo:     { icon: Sparkles, color: '#10b981' },
}
 
interface BloqueDisp { hora_inicio: string; hora_fin: string }
 
// ─── Paso colapsable ──────────────────────────────────────────────────────────
function Paso({ numero, titulo, completo, activo, resumen, onEditar, children }: {
  numero: number; titulo: string; completo: boolean; activo: boolean
  resumen?: string; onEditar: () => void; children: React.ReactNode
}) {
  return (
    <div className="rounded-2xl overflow-hidden mb-3"
      style={{ background: 'var(--color-surface)', border: `1px solid ${activo ? 'rgba(0,212,170,0.3)' : 'var(--color-border)'}` }}>
      <button onClick={onEditar} className="w-full flex items-center gap-3 p-4 text-left">
        <div className="w-8 h-8 rounded-xl flex items-center justify-center text-sm font-bold shrink-0"
          style={{
            background: completo ? 'var(--color-teal)' : activo ? 'rgba(0,212,170,0.15)' : 'var(--color-bg)',
            color: completo ? 'var(--color-navy)' : activo ? 'var(--color-teal)' : 'var(--color-text-3)',
            fontFamily: 'var(--font-display)',
          }}>
          {completo ? <Check size={16} /> : numero}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold" style={{ color: activo || completo ? 'var(--color-text-1)' : 'var(--color-text-3)' }}>
            {titulo}
          </p>
          {completo && resumen && !activo && (
            <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--color-teal)' }}>{resumen}</p>
          )}
        </div>
        {completo && !activo && <span className="text-xs font-medium shrink-0" style={{ color: 'var(--color-text-3)' }}>Editar</span>}
      </button>
      <AnimatePresence>
        {activo && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden">
            <div className="px-4 pb-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
 
function NuevoTurno() {
  const queryClient = useQueryClient()
  const [pasoActivo, setPasoActivo] = useState(1)
 
  // Selecciones
  const [cliente, setCliente]       = useState<Cliente | null>(null)
  const [servicio, setServicio]     = useState<Servicio | null>(null)
  const [trabajador, setTrabajador] = useState<Trabajador | null>(null)
  const [fecha, setFecha]           = useState<Date>(new Date())
  const [hora, setHora]             = useState<string | null>(null)
  const [notas, setNotas]           = useState('')
  const [exito, setExito]           = useState(false)
 
  // Búsqueda de cliente
  const [busquedaCliente, setBusquedaCliente] = useState('')
  const [creandoCliente, setCreandoCliente]   = useState(false)
  const [nuevoNombre, setNuevoNombre]         = useState('')
  const [nuevoTelefono, setNuevoTelefono]     = useState('')
 
  const { data: clientesData } = useQuery({
    queryKey: ['clientes-buscar', busquedaCliente],
    queryFn: () => clientesApi.listar({ q: busquedaCliente || undefined, por_pagina: 8 }).then(r => r.data),
    enabled: pasoActivo === 1,
  })
  const clientes: Cliente[] = clientesData?.items || []
 
  const { data: serviciosData } = useQuery<Servicio[]>({
    queryKey: ['servicios'],
    queryFn: () => serviciosApi.listar().then(r => r.data),
  })
  const servicios = (serviciosData || []).filter(s => s.activo)
 
  const { data: trabajadoresData } = useQuery<Trabajador[]>({
    queryKey: ['trabajadores'],
    queryFn: () => trabajadoresApi.listar().then(r => r.data),
  })
  const trabajadores = (trabajadoresData || []).filter(t => t.activo)
 
  // Disponibilidad real del trabajador
  const { data: dispData, isLoading: cargandoDisp } = useQuery<{ bloques: BloqueDisp[] }>({
    queryKey: ['disponibilidad', trabajador?.id, format(fecha, 'yyyy-MM-dd'), servicio?.duracion_minutos],
    queryFn: () => trabajadoresApi.disponibilidad(trabajador!.id, format(fecha, 'yyyy-MM-dd'), servicio!.duracion_minutos).then(r => r.data),
    enabled: !!trabajador && !!servicio && pasoActivo === 4,
  })
  const bloques: BloqueDisp[] = dispData?.bloques || []
 
  // Crear cliente al vuelo
  const crearCliente = useMutation({
    mutationFn: () => clientesApi.crear({ nombre: nuevoNombre, telefono: nuevoTelefono }),
    onSuccess: (r) => {
      setCliente(r.data); setCreandoCliente(false)
      setNuevoNombre(''); setNuevoTelefono('')
      setPasoActivo(2)
    },
  })
 
  // Crear turno
  const crearTurno = useMutation({
    mutationFn: () => turnosApi.crear({
      cliente_id: cliente!.id,
      trabajador_id: trabajador!.id,
      servicio_id: servicio!.id,
      fecha: format(fecha, 'yyyy-MM-dd'),
      hora_inicio: hora!,
      notas_cliente: notas || undefined,
      origen: 'presencial',
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['turnos-agenda'] })
      setExito(true)
    },
  })
 
  const resetear = () => {
    setExito(false); setCliente(null); setServicio(null); setTrabajador(null)
    setHora(null); setNotas(''); setPasoActivo(1); setBusquedaCliente('')
  }
 
  const fechaLabel = (d: Date) => isToday(d) ? 'Hoy' : isTomorrow(d) ? 'Mañana' : format(d, "EEE d/M", { locale: es })
 
  // ─── Pantalla de éxito ────────────────────────────────────────────────────
  if (exito) {
    return (
      <div className="p-8 max-w-2xl mx-auto flex flex-col items-center justify-center min-h-[70vh]">
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', bounce: 0.5 }}
          className="w-20 h-20 rounded-3xl flex items-center justify-center mb-6"
          style={{ background: 'rgba(0,212,170,0.12)', border: '2px solid var(--color-teal)' }}>
          <CheckCircle2 size={40} style={{ color: 'var(--color-teal)' }} />
        </motion.div>
        <motion.h2 initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="text-2xl font-bold mb-2" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
          ¡Turno reservado! 🎉
        </motion.h2>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
          className="text-sm text-center mb-8" style={{ color: 'var(--color-text-3)' }}>
          {cliente?.nombre} · {servicio?.nombre} con {trabajador?.nombre}<br />
          {fechaLabel(fecha)} a las {hora}
        </motion.p>
        <div className="flex gap-3">
          <button onClick={resetear} className="px-5 py-2.5 rounded-xl text-sm font-semibold"
            style={{ background: 'var(--color-teal)', color: 'var(--color-navy)', fontFamily: 'var(--font-display)' }}>
            Reservar otro turno
          </button>
          <a href="/agenda" className="px-5 py-2.5 rounded-xl text-sm font-medium"
            style={{ background: 'var(--color-surface)', color: 'var(--color-text-2)', border: '1px solid var(--color-border)' }}>
            Ver agenda
          </a>
        </div>
      </div>
    )
  }
 
  const puedeReservar = cliente && servicio && trabajador && hora
 
  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
          Nuevo turno
        </h1>
        <p className="text-sm mt-0.5" style={{ color: 'var(--color-text-3)' }}>
          Seguí los pasos para reservar
        </p>
      </div>
 
      {/* PASO 1: Cliente */}
      <Paso numero={1} titulo="Cliente" completo={!!cliente} activo={pasoActivo === 1}
        resumen={cliente ? `${cliente.nombre} ${cliente.apellido || ''}` : undefined}
        onEditar={() => setPasoActivo(1)}>
        {!creandoCliente ? (
          <div>
            <div className="relative mb-3">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-3)' }} />
              <input autoFocus type="text" placeholder="Buscar cliente por nombre o teléfono..."
                value={busquedaCliente} onChange={e => setBusquedaCliente(e.target.value)}
                className="w-full h-11 pl-10 pr-4 rounded-xl text-sm outline-none"
                style={{ background: 'var(--color-bg)', border: '1.5px solid var(--color-border)', color: 'var(--color-text-1)' }} />
            </div>
            <div className="space-y-1.5 max-h-64 overflow-y-auto">
              {clientes.map(c => {
                const n = NIVEL[c.nivel_fidelizacion] || NIVEL.nuevo
                return (
                  <button key={c.id} onClick={() => { setCliente(c); setPasoActivo(2) }}
                    className="w-full flex items-center gap-3 p-3 rounded-xl text-left transition-all"
                    style={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)' }}>
                    <div className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm shrink-0"
                      style={{ background: `${n.color}18`, color: n.color, fontFamily: 'var(--font-display)' }}>
                      {c.nombre.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold truncate" style={{ color: 'var(--color-text-1)' }}>
                        {c.nombre} {c.apellido || ''}
                      </p>
                      <p className="text-xs truncate" style={{ color: 'var(--color-text-3)' }}>
                        {c.telefono || 'Sin teléfono'} · {c.total_visitas} visitas
                      </p>
                    </div>
                    <ChevronRight size={15} style={{ color: 'var(--color-text-3)' }} />
                  </button>
                )
              })}
            </div>
            <button onClick={() => { setCreandoCliente(true); setNuevoNombre(busquedaCliente) }}
              className="w-full flex items-center justify-center gap-2 mt-3 py-2.5 rounded-xl text-sm font-medium"
              style={{ background: 'rgba(0,212,170,0.08)', color: 'var(--color-teal)', border: '1px dashed rgba(0,212,170,0.3)' }}>
              <UserPlus size={15} /> Crear cliente nuevo
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <input autoFocus type="text" placeholder="Nombre y apellido"
              value={nuevoNombre} onChange={e => setNuevoNombre(e.target.value)}
              className="w-full h-11 px-4 rounded-xl text-sm outline-none"
              style={{ background: 'var(--color-bg)', border: '1.5px solid var(--color-border)', color: 'var(--color-text-1)' }} />
            <input type="tel" placeholder="Teléfono"
              value={nuevoTelefono} onChange={e => setNuevoTelefono(e.target.value)}
              className="w-full h-11 px-4 rounded-xl text-sm outline-none"
              style={{ background: 'var(--color-bg)', border: '1.5px solid var(--color-border)', color: 'var(--color-text-1)' }} />
            <div className="flex gap-2">
              <button onClick={() => setCreandoCliente(false)} className="py-2.5 px-4 rounded-xl text-sm font-medium"
                style={{ background: 'var(--color-bg)', color: 'var(--color-text-2)', border: '1px solid var(--color-border)' }}>
                Cancelar
              </button>
              <button onClick={() => crearCliente.mutate()} disabled={!nuevoNombre.trim() || crearCliente.isPending}
                className="flex-1 py-2.5 rounded-xl text-sm font-bold disabled:opacity-50"
                style={{ background: 'var(--color-teal)', color: 'var(--color-navy)' }}>
                {crearCliente.isPending ? 'Creando...' : 'Crear y continuar'}
              </button>
            </div>
          </div>
        )}
      </Paso>
 
      {/* PASO 2: Servicio */}
      <Paso numero={2} titulo="Servicio" completo={!!servicio} activo={pasoActivo === 2}
        resumen={servicio ? `${servicio.nombre} · ${servicio.duracion_minutos}min · $${(servicio.precio_vigente || servicio.precio).toLocaleString('es-AR')}` : undefined}
        onEditar={() => cliente && setPasoActivo(2)}>
        <div className="grid grid-cols-2 gap-2">
          {servicios.map(s => (
            <button key={s.id} onClick={() => { setServicio(s); setPasoActivo(3) }}
              className="p-3 rounded-xl text-left transition-all"
              style={{ background: 'var(--color-bg)', border: `1.5px solid ${servicio?.id === s.id ? 'var(--color-teal)' : 'var(--color-border)'}` }}>
              <div className="flex items-center gap-2 mb-1">
                <Scissors size={13} style={{ color: 'var(--color-teal)' }} />
                <p className="text-sm font-semibold" style={{ color: 'var(--color-text-1)' }}>{s.nombre}</p>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs" style={{ color: 'var(--color-text-3)' }}>{s.duracion_minutos} min</span>
                <span className="text-sm font-bold" style={{ color: 'var(--color-teal)' }}>
                  ${(s.precio_vigente || s.precio).toLocaleString('es-AR')}
                </span>
              </div>
            </button>
          ))}
        </div>
      </Paso>
 
      {/* PASO 3: Trabajador */}
      <Paso numero={3} titulo="Profesional" completo={!!trabajador} activo={pasoActivo === 3}
        resumen={trabajador ? trabajador.nombre : undefined}
        onEditar={() => servicio && setPasoActivo(3)}>
        <div className="space-y-2">
          {trabajadores.map(t => (
            <button key={t.id} onClick={() => { setTrabajador(t); setHora(null); setPasoActivo(4) }}
              className="w-full flex items-center gap-3 p-3 rounded-xl text-left transition-all"
              style={{ background: 'var(--color-bg)', border: `1.5px solid ${trabajador?.id === t.id ? t.color_agenda : 'var(--color-border)'}` }}>
              <div className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm shrink-0"
                style={{ background: `${t.color_agenda}18`, color: t.color_agenda, fontFamily: 'var(--font-display)' }}>
                {t.nombre.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold" style={{ color: 'var(--color-text-1)' }}>{t.nombre} {t.apellido || ''}</p>
                {t.especialidades?.length > 0 && (
                  <p className="text-xs truncate" style={{ color: 'var(--color-text-3)' }}>{t.especialidades.join(' · ')}</p>
                )}
              </div>
              {t.calificacion_promedio > 0 && (
                <div className="flex items-center gap-1 shrink-0">
                  <Star size={11} style={{ color: '#f59e0b', fill: '#f59e0b' }} />
                  <span className="text-xs font-semibold" style={{ color: '#f59e0b' }}>{t.calificacion_promedio.toFixed(1)}</span>
                </div>
              )}
            </button>
          ))}
        </div>
      </Paso>
 
      {/* PASO 4: Fecha y hora */}
      <Paso numero={4} titulo="Fecha y horario" completo={!!hora} activo={pasoActivo === 4}
        resumen={hora ? `${fechaLabel(fecha)} a las ${hora}` : undefined}
        onEditar={() => trabajador && setPasoActivo(4)}>
        {/* Selector de fecha */}
        <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
          {Array.from({ length: 14 }).map((_, i) => {
            const d = addDays(new Date(), i)
            const sel = format(d, 'yyyy-MM-dd') === format(fecha, 'yyyy-MM-dd')
            return (
              <button key={i} onClick={() => { setFecha(d); setHora(null) }}
                className="flex flex-col items-center justify-center min-w-[60px] py-2 rounded-xl transition-all shrink-0"
                style={{ background: sel ? 'var(--color-navy)' : 'var(--color-bg)', border: `1.5px solid ${sel ? 'var(--color-teal)' : 'var(--color-border)'}` }}>
                <span className="text-xs font-medium capitalize" style={{ color: sel ? 'rgba(255,255,255,0.6)' : 'var(--color-text-3)' }}>
                  {format(d, 'EEE', { locale: es })}
                </span>
                <span className="text-lg font-bold" style={{ fontFamily: 'var(--font-display)', color: sel ? 'var(--color-teal)' : 'var(--color-text-1)' }}>
                  {format(d, 'd')}
                </span>
              </button>
            )
          })}
        </div>
 
        {/* Grilla de horarios */}
        {cargandoDisp ? (
          <div className="grid grid-cols-4 gap-2">
            {Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-10 rounded-xl animate-pulse" style={{ background: 'var(--color-border)' }} />)}
          </div>
        ) : bloques.length === 0 ? (
          <div className="flex flex-col items-center py-8 rounded-xl" style={{ background: 'var(--color-bg)' }}>
            <Clock size={24} className="mb-2" style={{ color: 'var(--color-text-3)' }} />
            <p className="text-sm font-medium" style={{ color: 'var(--color-text-2)' }}>Sin horarios disponibles</p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-3)' }}>Probá otro día o profesional</p>
          </div>
        ) : (
          <div className="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto">
            {bloques.map(b => {
              const sel = hora === b.hora_inicio
              return (
                <button key={b.hora_inicio} onClick={() => setHora(b.hora_inicio)}
                  className="py-2.5 rounded-xl text-sm font-semibold transition-all"
                  style={{
                    background: sel ? 'var(--color-teal)' : 'var(--color-bg)',
                    color: sel ? 'var(--color-navy)' : 'var(--color-text-1)',
                    border: `1.5px solid ${sel ? 'var(--color-teal)' : 'var(--color-border)'}`,
                  }}>
                  {b.hora_inicio.slice(0, 5)}
                </button>
              )
            })}
          </div>
        )}
      </Paso>
 
      {/* Resumen + confirmar */}
      <AnimatePresence>
        {puedeReservar && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="rounded-2xl p-5 mt-2" style={{ background: 'var(--color-navy)', border: '1px solid rgba(0,212,170,0.2)' }}>
            <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'rgba(255,255,255,0.4)' }}>
              Resumen del turno
            </p>
            <div className="space-y-2 mb-4">
              <div className="flex items-center gap-2 text-sm text-white">
                <User size={14} style={{ color: 'var(--color-teal)' }} /> {cliente?.nombre} {cliente?.apellido || ''}
              </div>
              <div className="flex items-center gap-2 text-sm text-white">
                <Scissors size={14} style={{ color: 'var(--color-teal)' }} /> {servicio?.nombre} · ${(servicio?.precio_vigente || servicio?.precio || 0).toLocaleString('es-AR')}
              </div>
              <div className="flex items-center gap-2 text-sm text-white">
                <User size={14} style={{ color: 'var(--color-teal)' }} /> {trabajador?.nombre}
              </div>
              <div className="flex items-center gap-2 text-sm text-white">
                <CalendarCheck size={14} style={{ color: 'var(--color-teal)' }} /> {fechaLabel(fecha)} a las {hora}
              </div>
            </div>
            <input type="text" placeholder="Nota opcional (ej: viene con referencia)"
              value={notas} onChange={e => setNotas(e.target.value)}
              className="w-full h-10 px-3 rounded-xl text-sm outline-none mb-3"
              style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }} />
            <button onClick={() => crearTurno.mutate()} disabled={crearTurno.isPending}
              className="w-full py-3 rounded-xl text-sm font-bold flex items-center justify-center gap-2 disabled:opacity-60"
              style={{ background: 'var(--color-teal)', color: 'var(--color-navy)', fontFamily: 'var(--font-display)' }}>
              {crearTurno.isPending ? 'Reservando...' : <><Zap size={16} /> Reservar turno</>}
            </button>
            {crearTurno.isError && (
              <p className="text-xs text-center mt-2" style={{ color: '#fca5a5' }}>
                No se pudo reservar. El horario puede estar ocupado.
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}






