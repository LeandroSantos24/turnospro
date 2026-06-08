'use client'
 
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { clientesApi } from '@/lib/api'
import { Cliente } from '@/types'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X, User, Phone, Mail, Gift, Heart, Scissors,
  Sparkles, ChevronDown, ChevronUp, Check, MessageCircle
} from 'lucide-react'
 
const GENEROS = [
  { value: 'masculino', label: 'Masculino' },
  { value: 'femenino', label: 'Femenino' },
  { value: 'no_binario', label: 'No binario' },
  { value: 'prefiero_no_decir', label: 'Prefiero no decir' },
]
 
const COMO_CONOCIO = [
  { value: 'instagram', label: 'Instagram' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'google', label: 'Google' },
  { value: 'referido', label: 'Me lo recomendaron' },
  { value: 'pasando', label: 'Pasando por el local' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'otro', label: 'Otro' },
]
 
// ─── Switch de consentimiento ─────────────────────────────────────────────────
function Toggle({ activo, onToggle, label, desc, icon: Icon, color }: {
  activo: boolean; onToggle: () => void; label: string; desc: string
  icon: React.ElementType; color: string
}) {
  return (
    <button type="button" onClick={onToggle}
      className="w-full flex items-center gap-3 p-3 rounded-xl text-left transition-all"
      style={{ background: activo ? `${color}10` : 'var(--color-bg)', border: `1px solid ${activo ? `${color}40` : 'var(--color-border)'}` }}>
      <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
        style={{ background: activo ? `${color}20` : 'var(--color-surface)' }}>
        <Icon size={16} style={{ color: activo ? color : 'var(--color-text-3)' }} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium" style={{ color: 'var(--color-text-1)' }}>{label}</p>
        <p className="text-xs" style={{ color: 'var(--color-text-3)' }}>{desc}</p>
      </div>
      <div className="w-10 h-6 rounded-full p-0.5 shrink-0 transition-all"
        style={{ background: activo ? color : 'var(--color-border)' }}>
        <motion.div className="w-5 h-5 rounded-full bg-white" animate={{ x: activo ? 16 : 0 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }} />
      </div>
    </button>
  )
}
 
// ─── Sección colapsable ───────────────────────────────────────────────────────
function Seccion({ titulo, abierto, onToggle, children }: {
  titulo: string; abierto: boolean; onToggle: () => void; children: React.ReactNode
}) {
  return (
    <div className="rounded-xl overflow-hidden" style={{ border: '1px solid var(--color-border)' }}>
      <button type="button" onClick={onToggle} className="w-full flex items-center justify-between p-3"
        style={{ background: 'var(--color-bg)' }}>
        <span className="text-sm font-medium" style={{ color: 'var(--color-text-2)' }}>{titulo}</span>
        {abierto ? <ChevronUp size={16} style={{ color: 'var(--color-text-3)' }} /> : <ChevronDown size={16} style={{ color: 'var(--color-text-3)' }} />}
      </button>
      <AnimatePresence>
        {abierto && (
          <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden">
            <div className="p-3 space-y-3">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
 
const inputCls = "w-full h-11 px-3 rounded-xl text-sm outline-none"
const inputStyle = { background: 'var(--color-bg)', border: '1.5px solid var(--color-border)', color: 'var(--color-text-1)' } as React.CSSProperties
 
export default function ClienteFormModal({ onClose, onCreado }: {
  onClose: () => void
  onCreado?: (c: Cliente) => void
}) {
  const queryClient = useQueryClient()
  const [seccionAbierta, setSeccionAbierta] = useState<string | null>('contacto')
 
  const [form, setForm] = useState<Record<string, unknown>>({
    nombre: '', telefono: '', apellido: '', email: '',
    dni: '', genero: '', direccion: '', telefono_alt: '', ocupacion: '',
    fecha_nacimiento: '', fecha_aniversario: '', estado_civil: '', como_conocio: '',
    tipo_cabello: '', tipo_piel: '', alergias: '',
    horario_preferido: '', dia_preferido: '', canal_preferido: '',
    observaciones_internas: '',
    acepta_recordatorios: true,
    acepta_promociones: true,
    acepta_cumpleanos: true,
  })
 
  const set = (k: string, v: unknown) => setForm(f => ({ ...f, [k]: v }))
 
  const crear = useMutation({
    mutationFn: () => {
      // Limpiar campos vacíos
      const payload: Record<string, unknown> = {}
      Object.entries(form).forEach(([k, v]) => {
        if (v !== '' && v !== null && v !== undefined) payload[k] = v
      })
      return clientesApi.crear(payload)
    },
    onSuccess: (r) => {
      queryClient.invalidateQueries({ queryKey: ['clientes'] })
      queryClient.invalidateQueries({ queryKey: ['clientes-todos'] })
      if (onCreado) onCreado(r.data)
      onClose()
    },
  })
 
  const valido = String(form.nombre).trim() && String(form.telefono).trim()
 
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}>
      <motion.div initial={{ opacity: 0, scale: 0.96, y: 12 }} animate={{ opacity: 1, scale: 1, y: 0 }}
        className="w-full max-w-lg rounded-3xl flex flex-col max-h-[90vh]"
        style={{ background: 'var(--color-surface)' }}>
 
        {/* Header */}
        <div className="flex items-center justify-between p-5" style={{ borderBottom: '1px solid var(--color-border)' }}>
          <div>
            <h3 className="font-bold text-lg" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}>
              Nuevo cliente
            </h3>
            <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-3)' }}>
              Solo el nombre y teléfono son necesarios
            </p>
          </div>
          <button onClick={onClose} className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'var(--color-bg)', color: 'var(--color-text-3)' }}>
            <X size={18} />
          </button>
        </div>
 
        {/* Body scrolleable */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
 
          {/* Datos básicos (siempre visible) */}
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--color-text-2)' }}>
                  Nombre <span style={{ color: 'var(--color-teal)' }}>*</span>
                </label>
                <input autoFocus value={String(form.nombre)} onChange={e => set('nombre', e.target.value)}
                  placeholder="Juan" className={inputCls} style={inputStyle} />
              </div>
              <div>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--color-text-2)' }}>Apellido</label>
                <input value={String(form.apellido)} onChange={e => set('apellido', e.target.value)}
                  placeholder="Pérez" className={inputCls} style={inputStyle} />
              </div>
            </div>
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--color-text-2)' }}>
                Teléfono <span style={{ color: 'var(--color-teal)' }}>*</span>
              </label>
              <input value={String(form.telefono)} onChange={e => set('telefono', e.target.value)}
                placeholder="2615123456" type="tel" className={inputCls} style={inputStyle} />
            </div>
            <div>
              <label className="text-xs font-medium mb-1.5 block flex items-center gap-1.5" style={{ color: 'var(--color-text-2)' }}>
                <Mail size={12} /> Email <span className="font-normal" style={{ color: 'var(--color-text-3)' }}>· para recordatorios</span>
              </label>
              <input value={String(form.email)} onChange={e => set('email', e.target.value)}
                placeholder="juan@email.com" type="email" className={inputCls} style={inputStyle} />
            </div>
          </div>
 
          {/* Más datos */}
          <Seccion titulo="📋 Más datos (opcional)" abierto={seccionAbierta === 'contacto'} onToggle={() => setSeccionAbierta(seccionAbierta === 'contacto' ? null : 'contacto')}>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--color-text-2)' }}>DNI</label>
                <input value={String(form.dni)} onChange={e => set('dni', e.target.value)} className={inputCls} style={inputStyle} />
              </div>
              <div>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--color-text-2)' }}>Género</label>
                <select value={String(form.genero)} onChange={e => set('genero', e.target.value)} className={inputCls} style={inputStyle}>
                  <option value="">—</option>
                  {GENEROS.map(g => <option key={g.value} value={g.value}>{g.label}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--color-text-2)' }}>Dirección</label>
              <input value={String(form.direccion)} onChange={e => set('direccion', e.target.value)} className={inputCls} style={inputStyle} />
            </div>
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--color-text-2)' }}>Ocupación</label>
              <input value={String(form.ocupacion)} onChange={e => set('ocupacion', e.target.value)} placeholder="Ej: docente, comerciante" className={inputCls} style={inputStyle} />
            </div>
          </Seccion>
 
          {/* Fidelización */}
          <Seccion titulo="🎁 Fidelización (opcional)" abierto={seccionAbierta === 'fidelizacion'} onToggle={() => setSeccionAbierta(seccionAbierta === 'fidelizacion' ? null : 'fidelizacion')}>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium mb-1.5 block flex items-center gap-1" style={{ color: 'var(--color-text-2)' }}>
                  <Gift size={11} /> Cumpleaños
                </label>
                <input type="date" value={String(form.fecha_nacimiento)} onChange={e => set('fecha_nacimiento', e.target.value)} className={inputCls} style={inputStyle} />
              </div>
              <div>
                <label className="text-xs font-medium mb-1.5 block flex items-center gap-1" style={{ color: 'var(--color-text-2)' }}>
                  <Heart size={11} /> Aniversario
                </label>
                <input type="date" value={String(form.fecha_aniversario)} onChange={e => set('fecha_aniversario', e.target.value)} className={inputCls} style={inputStyle} />
              </div>
            </div>
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--color-text-2)' }}>¿Cómo nos conoció?</label>
              <select value={String(form.como_conocio)} onChange={e => set('como_conocio', e.target.value)} className={inputCls} style={inputStyle}>
                <option value="">—</option>
                {COMO_CONOCIO.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
          </Seccion>
 
          {/* Datos del servicio */}
          <Seccion titulo="✂️ Datos del servicio (opcional)" abierto={seccionAbierta === 'servicio'} onToggle={() => setSeccionAbierta(seccionAbierta === 'servicio' ? null : 'servicio')}>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--color-text-2)' }}>Tipo de cabello</label>
                <input value={String(form.tipo_cabello)} onChange={e => set('tipo_cabello', e.target.value)} placeholder="Lacio, rizado..." className={inputCls} style={inputStyle} />
              </div>
              <div>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--color-text-2)' }}>Tipo de piel</label>
                <input value={String(form.tipo_piel)} onChange={e => set('tipo_piel', e.target.value)} placeholder="Grasa, seca..." className={inputCls} style={inputStyle} />
              </div>
            </div>
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: '#ef4444' }}>⚠️ Alergias</label>
              <input value={String(form.alergias)} onChange={e => set('alergias', e.target.value)} placeholder="Ej: alergia a tintura X" className={inputCls} style={inputStyle} />
            </div>
            <div>
              <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--color-text-2)' }}>Notas internas</label>
              <textarea value={String(form.observaciones_internas)} onChange={e => set('observaciones_internas', e.target.value)}
                rows={2} placeholder="Cualquier cosa para recordar de este cliente"
                className="w-full px-3 py-2 rounded-xl text-sm outline-none resize-none" style={inputStyle} />
            </div>
          </Seccion>
 
          {/* Consentimientos */}
          <div className="space-y-2">
            <p className="text-xs font-medium" style={{ color: 'var(--color-text-3)' }}>El cliente acepta recibir:</p>
            <Toggle activo={!!form.acepta_recordatorios} onToggle={() => set('acepta_recordatorios', !form.acepta_recordatorios)}
              label="Recordatorios de turno" desc="Avisos antes de cada cita" icon={MessageCircle} color="#3b82f6" />
            <Toggle activo={!!form.acepta_promociones} onToggle={() => set('acepta_promociones', !form.acepta_promociones)}
              label="Promociones y ofertas" desc="Descuentos y novedades" icon={Sparkles} color="#f59e0b" />
            <Toggle activo={!!form.acepta_cumpleanos} onToggle={() => set('acepta_cumpleanos', !form.acepta_cumpleanos)}
              label="Saludo de cumpleaños" desc="Regalito en su día especial" icon={Gift} color="#a855f7" />
          </div>
        </div>
 
        {/* Footer */}
        <div className="p-5 flex gap-3" style={{ borderTop: '1px solid var(--color-border)' }}>
          <button onClick={onClose} className="px-5 py-3 rounded-xl text-sm font-medium"
            style={{ background: 'var(--color-bg)', color: 'var(--color-text-2)', border: '1px solid var(--color-border)' }}>
            Cancelar
          </button>
          <button onClick={() => crear.mutate()} disabled={!valido || crear.isPending}
            className="flex-1 py-3 rounded-xl text-sm font-bold flex items-center justify-center gap-2 disabled:opacity-50"
            style={{ background: 'var(--color-teal)', color: 'var(--color-navy)', fontFamily: 'var(--font-display)' }}>
            {crear.isPending ? 'Guardando...' : <><Check size={16} /> Guardar cliente</>}
          </button>
        </div>
        {crear.isError && (
          <p className="text-xs text-center pb-4" style={{ color: '#ef4444' }}>
            No se pudo guardar. Revisá los datos e intentá de nuevo.
          </p>
        )}
      </motion.div>
    </div>
  )
}