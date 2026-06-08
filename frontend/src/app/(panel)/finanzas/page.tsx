'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { pagosApi } from '@/lib/api'
import { motion } from 'framer-motion'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { format, subDays, startOfMonth } from 'date-fns'
import { es } from 'date-fns/locale'
import {
  Banknote, CreditCard, Smartphone, Building2,
  TrendingUp, TrendingDown, Receipt, Settings2,
  ChevronDown, ChevronUp, CheckCircle2, XCircle
} from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'

const qc = new QueryClient()
export default function FinanzasPage() {
  return <QueryClientProvider client={qc}><Finanzas /></QueryClientProvider>
}

const METODO_CFG: Record<string, { icon: React.ElementType; label: string; color: string; bg: string }> = {
  efectivo:      { icon: Banknote,    label: 'Efectivo',      color: '#10b981', bg: '#ecfdf5' },
  debito:        { icon: CreditCard,  label: 'Débito',        color: '#3b82f6', bg: '#eff6ff' },
  credito:       { icon: CreditCard,  label: 'Crédito',       color: '#f59e0b', bg: '#fffbeb' },
  mercadopago:   { icon: Smartphone,  label: 'MercadoPago',   color: '#8b5cf6', bg: '#f5f3ff' },
  transferencia: { icon: Building2,   label: 'Transferencia', color: '#64748b', bg: '#f8fafc' },
}

function MetodoCard({ metodo, bruto, comision, neto, pct }: {
  metodo: string; bruto: number; comision: number; neto: number; pct: number
}) {
  const cfg = METODO_CFG[metodo] || METODO_CFG.efectivo
  return (
    <div className="flex items-center gap-4 p-4 rounded-2xl"
      style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
      <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
        style={{ background: cfg.bg, border: `1px solid ${cfg.color}30` }}>
        <cfg.icon size={18} style={{ color: cfg.color }} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <p className="text-sm font-semibold" style={{ color: 'var(--color-text-1)' }}>{cfg.label}</p>
          <p className="text-sm font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-teal)' }}>
            ${neto.toLocaleString('es-AR')}
          </p>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex gap-3">
            <span className="text-xs" style={{ color: 'var(--color-text-3)' }}>
              Bruto ${bruto.toLocaleString('es-AR')}
            </span>
            {pct > 0 && (
              <span className="text-xs" style={{ color: '#ef4444' }}>
                -{pct}% (${comision.toLocaleString('es-AR')})
              </span>
            )}
          </div>
        </div>
        {/* Barra visual */}
        <div className="mt-2 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--color-bg)' }}>
          <motion.div className="h-full rounded-full"
            style={{ background: cfg.color }}
            initial={{ width: 0 }}
            animate={{ width: `${100 - pct}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }} />
        </div>
      </div>
    </div>
  )
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl px-3 py-2 text-xs shadow-lg"
      style={{ background: 'var(--color-navy)', color: 'white' }}>
      <p className="font-medium mb-1">{label}</p>
      <p>Bruto: <strong>${(payload[0]?.value || 0).toLocaleString('es-AR')}</strong></p>
      {payload[1] && <p style={{ color: 'var(--color-teal)' }}>Neto: <strong>${(payload[1].value || 0).toLocaleString('es-AR')}</strong></p>}
    </div>
  )
}

function Finanzas() {
  const [fechaCierre, setFechaCierre] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [expandirComisiones, setExpandirComisiones] = useState(false)

  const hoy = new Date()
  const desde = format(startOfMonth(hoy), 'yyyy-MM-dd')
  const hasta = format(hoy, 'yyyy-MM-dd')

  const { data: cierre, isLoading: cargandoCierre } = useQuery({
    queryKey: ['cierre-caja', fechaCierre],
    queryFn: () => pagosApi.cierreCaja(fechaCierre).then(r => r.data),
  })

  const { data: resumenMes } = useQuery({
    queryKey: ['resumen-periodo', desde, hasta],
    queryFn: () => pagosApi.resumenPeriodo ? 
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/pagos/resumen-periodo?fecha_desde=${desde}&fecha_hasta=${hasta}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
      }).then(r => r.json()) : Promise.resolve({ dias: [], totales: {} }),
  })

  const { data: comisiones } = useQuery({
    queryKey: ['comisiones'],
    queryFn: () => pagosApi.comisiones().then(r => r.data),
  })

  const dias = resumenMes?.dias || []
  const totalMes = resumenMes?.totales || { bruto: 0, neto: 0, comision: 0 }

  // Últimos 14 días para el gráfico
  const graficoDias = dias.slice(-14).map((d: { fecha: string; bruto: number; neto: number }) => ({
    fecha: format(new Date(d.fecha), 'd/M'),
    bruto: d.bruto,
    neto: d.neto,
  }))

  const c = cierre

  return (
    <div className="p-8 max-w-5xl mx-auto">

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
            Finanzas
          </h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--color-text-3)' }}>
            Facturación real después de comisiones
          </p>
        </div>
        <input type="date" value={fechaCierre}
          onChange={e => setFechaCierre(e.target.value)}
          className="h-10 px-3 rounded-xl text-sm outline-none"
          style={{ background: 'var(--color-surface)', border: '1.5px solid var(--color-border)', color: 'var(--color-text-2)' }} />
      </div>

      {/* Resumen del mes */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { label: 'Bruto del mes',   value: totalMes.bruto,    color: 'var(--color-text-1)', sub: 'Lo que facturaste' },
          { label: 'Comisiones',      value: totalMes.comision, color: '#ef4444',             sub: 'Lo que perdés en métodos' },
          { label: 'Neto del mes',    value: totalMes.neto,     color: 'var(--color-teal)',   sub: 'Lo que queda en el bolsillo' },
        ].map(k => (
          <motion.div key={k.label} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl p-5" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
            <p className="text-2xl font-bold mb-1" style={{ fontFamily: 'var(--font-display)', color: k.color }}>
              ${(k.value || 0).toLocaleString('es-AR')}
            </p>
            <p className="text-sm font-medium" style={{ color: 'var(--color-text-2)' }}>{k.label}</p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-3)' }}>{k.sub}</p>
          </motion.div>
        ))}
      </div>

      {/* Gráfico de evolución */}
      {graficoDias.length > 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          className="rounded-2xl p-6 mb-6" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-sm" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
                Evolución del mes
              </h3>
              <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-3)' }}>Bruto vs neto por día</p>
            </div>
            <div className="flex items-center gap-4 text-xs" style={{ color: 'var(--color-text-3)' }}>
              <span className="flex items-center gap-1.5">
                <div className="w-3 h-0.5 rounded" style={{ background: '#e2e8f0' }} /> Bruto
              </span>
              <span className="flex items-center gap-1.5">
                <div className="w-3 h-0.5 rounded" style={{ background: 'var(--color-teal)' }} /> Neto
              </span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={graficoDias} margin={{ top: 5, right: 5, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="gBruto" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#e2e8f0" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#e2e8f0" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gNeto" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d4aa" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00d4aa" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="fecha" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis hide />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="bruto" stroke="#e2e8f0" strokeWidth={2} fill="url(#gBruto)" />
              <Area type="monotone" dataKey="neto"  stroke="#00d4aa" strokeWidth={2} fill="url(#gNeto)" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* Cierre de caja del día */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">

        {/* Resumen del día */}
        <div className="rounded-2xl p-6" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <h3 className="font-semibold text-sm mb-4" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
            Cierre del {format(new Date(fechaCierre + 'T12:00:00'), "d 'de' MMMM", { locale: es })}
          </h3>
          {cargandoCierre ? (
            <div className="space-y-3">
              {[1,2,3].map(i => <div key={i} className="h-10 rounded-xl animate-pulse" style={{ background: 'var(--color-border)' }} />)}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl" style={{ background: 'var(--color-bg)' }}>
                <span className="text-sm" style={{ color: 'var(--color-text-2)' }}>Turnos del día</span>
                <span className="text-sm font-semibold" style={{ color: 'var(--color-text-1)' }}>
                  {c?.turnos_atendidos || 0} atendidos / {c?.total_turnos || 0} total
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl" style={{ background: 'var(--color-bg)' }}>
                <span className="text-sm" style={{ color: 'var(--color-text-2)' }}>Facturado bruto</span>
                <span className="text-sm font-semibold" style={{ color: 'var(--color-text-1)' }}>
                  ${(c?.monto_bruto_total || 0).toLocaleString('es-AR')}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl" style={{ background: '#fef2f2', border: '1px solid #fca5a525' }}>
                <span className="text-sm" style={{ color: '#ef4444' }}>Comisiones pagadas</span>
                <span className="text-sm font-semibold" style={{ color: '#ef4444' }}>
                  -${(c?.comision_total || 0).toLocaleString('es-AR')}
                </span>
              </div>
              <div className="flex items-center justify-between p-4 rounded-xl" style={{ background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.25)' }}>
                <span className="text-base font-semibold" style={{ color: 'var(--color-text-1)' }}>Neto real</span>
                <span className="text-xl font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-teal)' }}>
                  ${(c?.monto_neto_total || 0).toLocaleString('es-AR')}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 pt-1">
                <div className="flex items-center gap-2 p-3 rounded-xl"
                  style={{ background: c?.facturado_monto ? '#ecfdf5' : 'var(--color-bg)', border: '1px solid var(--color-border)' }}>
                  {c?.facturado_monto ? <CheckCircle2 size={14} style={{ color: '#10b981' }} /> : <XCircle size={14} style={{ color: '#94a3b8' }} />}
                  <div>
                    <p className="text-xs font-medium" style={{ color: 'var(--color-text-2)' }}>Facturado</p>
                    <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>${(c?.facturado_monto || 0).toLocaleString('es-AR')}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 p-3 rounded-xl" style={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)' }}>
                  <Receipt size={14} style={{ color: '#94a3b8' }} />
                  <div>
                    <p className="text-xs font-medium" style={{ color: 'var(--color-text-2)' }}>Sin factura</p>
                    <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>${(c?.no_facturado_monto || 0).toLocaleString('es-AR')}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Desglose por método */}
        <div className="rounded-2xl p-6" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <h3 className="font-semibold text-sm mb-4" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
            Desglose por método
          </h3>
          {!c?.por_metodo?.length ? (
            <div className="flex items-center justify-center py-12" style={{ color: 'var(--color-text-3)', fontSize: '13px' }}>
              Sin pagos registrados en este día
            </div>
          ) : (
            <div className="space-y-3">
              {c.por_metodo.map((m: { metodo: string; monto_bruto: number; comision_monto: number; monto_neto: number; comision_porcentaje: number }) => (
                <MetodoCard key={m.metodo}
                  metodo={m.metodo} bruto={m.monto_bruto}
                  comision={m.comision_monto} neto={m.monto_neto}
                  pct={m.comision_porcentaje} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Configuración de comisiones */}
      <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
        <button onClick={() => setExpandirComisiones(!expandirComisiones)}
          className="w-full flex items-center justify-between p-5 text-left"
          style={{ borderBottom: expandirComisiones ? '1px solid var(--color-border)' : 'none' }}>
          <div className="flex items-center gap-3">
            <Settings2 size={16} style={{ color: 'var(--color-text-3)' }} />
            <span className="text-sm font-semibold" style={{ color: 'var(--color-text-1)' }}>
              Comisiones configuradas
            </span>
          </div>
          {expandirComisiones ? <ChevronUp size={16} style={{ color: 'var(--color-text-3)' }} /> : <ChevronDown size={16} style={{ color: 'var(--color-text-3)' }} />}
        </button>
        {expandirComisiones && comisiones && (
          <div className="p-5 grid grid-cols-2 gap-3">
            {Object.entries(comisiones.comisiones || {}).map(([metodo, pct]) => {
              const cfg = METODO_CFG[metodo] || METODO_CFG.efectivo
              return (
                <div key={metodo} className="flex items-center justify-between p-3 rounded-xl"
                  style={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)' }}>
                  <div className="flex items-center gap-2">
                    <cfg.icon size={14} style={{ color: cfg.color }} />
                    <span className="text-sm" style={{ color: 'var(--color-text-2)' }}>{cfg.label}</span>
                  </div>
                  <span className="text-sm font-bold" style={{ color: Number(pct) > 0 ? '#ef4444' : '#10b981' }}>
                    {Number(pct) === 0 ? 'Sin costo' : `${pct}%`}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}