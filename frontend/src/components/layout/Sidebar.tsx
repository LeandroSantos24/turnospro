'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuthStore } from '@/store/auth'
import {
  LayoutDashboard, Calendar, Users, Clock,
  Banknote, UserCog, Scissors, Settings,
  LogOut, ChevronRight, Zap
} from 'lucide-react'

const nav = [
  { href: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard',    group: 'main' },
  { href: '/agenda',        icon: Calendar,        label: 'Agenda',       group: 'main' },
  { href: '/turnos',        icon: Clock,           label: 'Turnos',       group: 'main' },
  { href: '/clientes',      icon: Users,           label: 'Clientes',     group: 'main' },
  { href: '/finanzas',      icon: Banknote,        label: 'Finanzas',     group: 'negocio' },
  { href: '/trabajadores',  icon: UserCog,         label: 'Trabajadores', group: 'negocio' },
  { href: '/servicios',     icon: Scissors,        label: 'Servicios',    group: 'negocio' },
  { href: '/configuracion', icon: Settings,        label: 'Config.',      group: 'sistema' },
]

const groups = [
  { id: 'main',    label: 'Principal' },
  { id: 'negocio', label: 'Negocio' },
  { id: 'sistema', label: 'Sistema' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const router   = useRouter()
  const { user, logout } = useAuthStore()

  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  const planColors: Record<string, string> = {
    pro:        '#00d4aa',
    enterprise: '#f59e0b',
    free:       '#94a3b8',
  }
  const planColor = planColors[user?.plan || 'free'] || '#94a3b8'

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="w-60 flex flex-col h-full shrink-0"
      style={{ background: 'var(--color-navy)', borderRight: '1px solid rgba(255,255,255,0.06)' }}
    >
      {/* Logo */}
      <div className="px-5 pt-6 pb-5" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-base shrink-0 transition-transform group-hover:scale-105"
            style={{
              background: 'var(--color-teal)',
              color: 'var(--color-navy)',
              fontFamily: 'var(--font-display)',
            }}
          >
            T
          </div>
          <div>
            <div
              className="text-white font-semibold leading-none"
              style={{ fontFamily: 'var(--font-display)', fontSize: '16px' }}
            >
              Turno360
            </div>
            <div className="text-xs mt-0.5 font-medium" style={{ color: planColor }}>
              Plan {user?.plan || 'free'}
            </div>
          </div>
        </Link>
      </div>

      {/* Navegación */}
      <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
        {groups.map((group) => {
          const items = nav.filter((n) => n.group === group.id)
          return (
            <div key={group.id}>
              <p
                className="text-xs font-semibold px-2 mb-1.5 uppercase tracking-widest"
                style={{ color: 'rgba(255,255,255,0.25)' }}
              >
                {group.label}
              </p>
              <div className="space-y-0.5">
                {items.map((item) => {
                  const isActive = pathname === item.href ||
                    (item.href !== '/dashboard' && pathname.startsWith(item.href))
                  return (
                    <Link key={item.href} href={item.href}>
                      <div
                        className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group relative"
                        style={{
                          background:   isActive ? 'rgba(0,212,170,0.12)' : 'transparent',
                          color:        isActive ? 'var(--color-teal)' : 'rgba(255,255,255,0.55)',
                        }}
                      >
                        {isActive && (
                          <motion.div
                            layoutId="active-pill"
                            className="absolute inset-0 rounded-xl"
                            style={{ background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.2)' }}
                            transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}
                          />
                        )}
                        <item.icon
                          size={17}
                          className="relative z-10 shrink-0 transition-colors"
                          style={{ color: isActive ? 'var(--color-teal)' : 'rgba(255,255,255,0.4)' }}
                        />
                        <span className="relative z-10">{item.label}</span>
                        {isActive && (
                          <ChevronRight size={14} className="ml-auto relative z-10" style={{ color: 'var(--color-teal)' }} />
                        )}
                      </div>
                    </Link>
                  )
                })}
              </div>
            </div>
          )
        })}
      </nav>

      {/* Usuario + Logout */}
      <div className="px-3 pb-4" style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '12px' }}>
        {/* Upgrade badge para plan free */}
        {user?.plan === 'free' && (
          <div
            className="flex items-center gap-2 px-3 py-2.5 rounded-xl mb-3 cursor-pointer hover:opacity-80 transition-opacity"
            style={{ background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.2)' }}
          >
            <Zap size={14} style={{ color: 'var(--color-teal)' }} />
            <span className="text-xs font-medium" style={{ color: 'var(--color-teal)' }}>
              Mejorar a Pro
            </span>
          </div>
        )}

        <div className="flex items-center gap-3 px-2 py-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-semibold shrink-0"
            style={{
              background: 'var(--color-navy-600)',
              color: 'var(--color-teal)',
              border: '1px solid rgba(0,212,170,0.2)',
              fontFamily: 'var(--font-display)',
            }}
          >
            {user?.nombre?.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.nombre}</p>
            <p className="text-xs truncate" style={{ color: 'rgba(255,255,255,0.35)' }}>{user?.rol}</p>
          </div>
          <button
            onClick={handleLogout}
            className="p-1.5 rounded-lg transition-colors hover:bg-white/10"
            style={{ color: 'rgba(255,255,255,0.35)' }}
            title="Cerrar sesión"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </motion.aside>
  )
}