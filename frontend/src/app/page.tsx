'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/auth'

export default function Home() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()

  useEffect(() => {
    router.replace(isAuthenticated ? '/dashboard' : '/login')
  }, [isAuthenticated, router])

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--color-navy)' }}>
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-xl animate-pulse"
          style={{ background: 'var(--color-teal)', color: 'var(--color-navy)', fontFamily: 'var(--font-display)' }}>
          T
        </div>
        <div className="w-6 h-6 border-2 rounded-full animate-spin"
          style={{ borderColor: 'rgba(0,212,170,0.2)', borderTopColor: 'var(--color-teal)' }} />
      </div>
    </div>
  )
}