'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { serviciosApi } from '@/lib/api'
import { Servicio } from '@/types'
import { motion } from 'framer-motion'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Scissors, Clock, Star, Plus, TrendingUp, Tag } from 'lucide-react'

const qc = new QueryClient()
export default function ServiciosPage() {
  return <QueryClientProvider client={qc}><Servicios /></QueryClientProvider>
}

function ServicioCard({ s }: { s: Servicio }) {
  const tieneDescuento = s.precio_descuento && s.precio_descuento < s.precio
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl p-5 group cursor-pointer relative overflow-hidden"
      style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
      {s.destacado && (
        <div className="absolute top-0 right-0 px-3 py-1 rounded-bl-xl text-xs font-semibold flex items-center gap-1"
          style={{ background: 'rgba(245,158,11,0.12)', color: '#f59e0b' }}>
          <Star size={10} /> Destacado
        </div>
      )}
      <div className="flex items-start gap-3 mb-4">
        <div className="w-11 h-11 rounded-2xl flex items-center justify-center shrink-0"
          style={{ background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.2)' }}>
          <Scissors size={18} style={{ color: 'var(--color-teal)' }} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm" style={{ color: 'var(--color-text-1)' }}>{s.nombre}</p>
          {s.descripcion && (
            <p className="text-xs mt-0.5 line-clamp-2" style={{ color: 'var(--color-text-3)' }}>{s.descripcion}</p>
          )}
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--color-text-3)' }}>
          <Clock size={12} /> {s.duracion_minutos} min
        </div>
        <div className="text-right">
          {tieneDescuento ? (
            <div className="flex items-center gap-2">
              <span className="text-xs line-through" style={{ color: 'var(--color-text-3)' }}>
                ${s.precio.toLocaleString('es-AR')}
              </span>
              <span className="text-lg font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-teal)' }}>
                ${(s.precio_descuento || 0).toLocaleString('es-AR')}
              </span>
            </div>
          ) : (
            <span className="text-lg font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
              ${s.precio.toLocaleString('es-AR')}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  )
}

function Servicios() {
  const { data, isLoading } = useQuery<Servicio[]>({
    queryKey: ['servicios'],
    queryFn: () => serviciosApi.listar().then(r => r.data),
  })

  const servicios = data || []
  const activos = servicios.filter(s => s.activo)
  const precioPromedio = activos.length > 0
    ? activos.reduce((sum, s) => sum + (s.precio_vigente || s.precio), 0) / activos.length
    : 0

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
            Servicios
          </h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--color-text-3)' }}>
            {activos.length} servicios activos · precio promedio ${precioPromedio.toLocaleString('es-AR', { maximumFractionDigits: 0 })}
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold"
          style={{ background: 'var(--color-teal)', color: 'var(--color-navy)', fontFamily: 'var(--font-display)' }}>
          <Plus size={16} /> Nuevo servicio
        </button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
          {[1,2,3].map(i => <div key={i} className="h-40 rounded-2xl animate-pulse" style={{ background: 'var(--color-border)' }} />)}
        </div>
      ) : servicios.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
            style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
            <Scissors size={28} style={{ color: 'var(--color-text-3)' }} />
          </div>
          <p className="font-semibold" style={{ color: 'var(--color-text-2)' }}>Sin servicios todavía</p>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-3)' }}>Agregá tu primer servicio</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 xl:grid-cols-3 gap-4 stagger">
          {servicios.map(s => <ServicioCard key={s.id} s={s} />)}
        </div>
      )}
    </div>
  )
}