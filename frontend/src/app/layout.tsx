import type { Metadata } from 'next'
import { TooltipProvider } from '@/components/ui/tooltip'
import '@/app/globals.css'

export const metadata: Metadata = {
  title: 'Turno360 — Sistema de gestión profesional',
  description: 'Gestión de turnos, CRM y automatización para tu negocio',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body>
        <TooltipProvider>
          {children}
        </TooltipProvider>
      </body>
    </html>
  )
}