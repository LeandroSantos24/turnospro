'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuthStore } from '@/store/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Eye, EyeOff, Calendar, Users, TrendingUp, Zap } from 'lucide-react'

const features = [
  { icon: Calendar, label: 'Turnos en tiempo real' },
  { icon: Users,    label: 'CRM inteligente' },
  { icon: TrendingUp, label: 'Analytics avanzado' },
  { icon: Zap,      label: 'Automatización WhatsApp' },
]

export default function LoginPage() {
  const router   = useRouter()
  const { login, isLoading } = useAuthStore()

  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [error,    setError]    = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await login(email, password)
      router.push('/dashboard')
    } catch {
      setError('Email o contraseña incorrectos')
    }
  }

  return (
    <div className="min-h-screen flex">

      {/* ── Panel izquierdo — marca ── */}
      <div
        className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 relative overflow-hidden"
        style={{ background: 'var(--color-navy)' }}
      >
        {/* Círculos decorativos */}
        <div
          className="absolute -top-32 -right-32 w-96 h-96 rounded-full opacity-10"
          style={{ background: 'radial-gradient(circle, var(--color-teal) 0%, transparent 70%)' }}
        />
        <div
          className="absolute -bottom-24 -left-24 w-80 h-80 rounded-full opacity-5"
          style={{ background: 'radial-gradient(circle, var(--color-teal) 0%, transparent 70%)' }}
        />
        <div
          className="absolute top-1/3 left-1/4 w-64 h-64 rounded-full opacity-5"
          style={{ background: 'radial-gradient(circle, #3b82f6 0%, transparent 70%)' }}
        />

        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-lg"
              style={{
                background: 'var(--color-teal)',
                color: 'var(--color-navy)',
                fontFamily: 'var(--font-display)',
              }}
            >
              T
            </div>
            <span
              className="text-2xl font-semibold text-white"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              TurnosPro
            </span>
          </div>
        </motion.div>

        {/* Tagline central */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="space-y-6"
        >
          <h1
            className="text-5xl font-bold leading-tight text-white"
            style={{ fontFamily: 'var(--font-display)' }}
          >
            El sistema que tu negocio
            <span style={{ color: 'var(--color-teal)' }}> merece.</span>
          </h1>
          <p className="text-lg leading-relaxed" style={{ color: 'rgba(255,255,255,0.55)' }}>
            Gestión de turnos, CRM profundo y automatización inteligente
            para negocios que quieren crecer.
          </p>

          {/* Feature pills */}
          <div className="flex flex-wrap gap-3 pt-2">
            {features.map((f, i) => (
              <motion.div
                key={f.label}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.1 }}
                className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium"
                style={{
                  background: 'rgba(255,255,255,0.07)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: 'rgba(255,255,255,0.8)',
                }}
              >
                <f.icon size={14} style={{ color: 'var(--color-teal)' }} />
                {f.label}
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-sm"
          style={{ color: 'rgba(255,255,255,0.3)' }}
        >
          © 2026 TurnosPro · Hecho en Argentina 🇦🇷
        </motion.div>
      </div>

      {/* ── Panel derecho — formulario ── */}
      <div
        className="flex-1 flex flex-col items-center justify-center p-8"
        style={{ background: 'var(--color-bg)' }}
      >
        {/* Logo mobile */}
        <div className="flex items-center gap-2 mb-10 lg:hidden">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center font-bold"
            style={{ background: 'var(--color-teal)', color: 'var(--color-navy)', fontFamily: 'var(--font-display)' }}
          >T</div>
          <span className="text-xl font-semibold" style={{ fontFamily: 'var(--font-display)' }}>TurnosPro</span>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="w-full max-w-md"
        >
          {/* Header del form */}
          <div className="mb-8">
            <h2
              className="text-3xl font-bold mb-2"
              style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-1)' }}
            >
              Bienvenido
            </h2>
            <p style={{ color: 'var(--color-text-2)' }}>
              Ingresá a tu panel de gestión
            </p>
          </div>

          {/* Formulario */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email" style={{ color: 'var(--color-text-2)', fontSize: '13px', fontWeight: 500 }}>
                Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="admin@tunegocio.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                style={{
                  height: '48px',
                  border: '1.5px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '14px',
                }}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" style={{ color: 'var(--color-text-2)', fontSize: '13px', fontWeight: 500 }}>
                Contraseña
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPass ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  style={{
                    height: '48px',
                    border: '1.5px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '14px',
                    paddingRight: '44px',
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                  style={{ color: 'var(--color-text-3)' }}
                >
                  {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-sm px-4 py-3 rounded-lg"
                style={{
                  background: 'var(--color-danger-bg)',
                  color: 'var(--color-danger)',
                  border: '1px solid rgba(239,68,68,0.2)',
                }}
              >
                {error}
              </motion.p>
            )}

            {/* Botón */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full font-semibold text-base transition-all duration-200 hover:opacity-90 active:scale-[0.99]"
              style={{
                height: '48px',
                background: isLoading ? 'var(--color-teal-dark)' : 'var(--color-teal)',
                color: 'var(--color-navy)',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                fontFamily: 'var(--font-display)',
                letterSpacing: '0.01em',
              }}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                  </svg>
                  Ingresando...
                </span>
              ) : (
                'Ingresar al panel'
              )}
            </Button>
          </form>

          {/* Credenciales de demo */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="mt-8 p-4 rounded-xl"
            style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
            }}
          >
            <p className="text-xs font-semibold mb-2" style={{ color: 'var(--color-text-3)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Cuenta de demo
            </p>
            <div className="space-y-1">
              <p className="text-sm" style={{ color: 'var(--color-text-2)' }}>
                <span style={{ color: 'var(--color-text-3)' }}>Email: </span>
                <code className="text-xs px-1.5 py-0.5 rounded" style={{ background: 'var(--color-surface-2)', color: 'var(--color-text-1)' }}>
                  admin@barberia.com
                </code>
              </p>
              <p className="text-sm" style={{ color: 'var(--color-text-2)' }}>
                <span style={{ color: 'var(--color-text-3)' }}>Clave: </span>
                <code className="text-xs px-1.5 py-0.5 rounded" style={{ background: 'var(--color-surface-2)', color: 'var(--color-text-1)' }}>
                  Admin123!
                </code>
              </p>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}