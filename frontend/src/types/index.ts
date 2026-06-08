// types/index.ts — Todos los tipos TypeScript del sistema

export interface Usuario {
  id: string
  empresa_id: string
  nombre: string
  apellido: string | null
  email: string
  rol: 'admin' | 'recepcionista' | 'trabajador'
  activo: boolean
  email_verificado: boolean
  ultimo_login: string | null
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  usuario: {
    id: string
    nombre: string
    apellido: string | null
    email: string
    rol: string
    plan: string
  }
}

export interface Cliente {
  id: string
  empresa_id: string
  nombre: string
  apellido: string | null
  email: string | null
  telefono: string
  estado: 'activo' | 'inactivo' | 'bloqueado'
  nivel_fidelizacion: 'nuevo' | 'regular' | 'frecuente' | 'vip'
  total_visitas: number
  total_gastado: number
  ultima_visita: string | null
  created_at: string
  tipo_cabello?: string | null
  tipo_piel?: string | null
  alergias?: string | null
  observaciones_internas?: string | null
  notas_ultimo_servicio?: string | null
  etiquetas?: string[]
  intereses?: string[]
  como_conocio?: string | null
}

export interface PaginatedClientes {
  items: Cliente[]
  total: number
  pagina: number
  por_pagina: number
  paginas: number
}

export interface Trabajador {
  id: string
  nombre: string
  apellido: string | null
  email: string | null
  telefono: string | null
  foto_url: string | null
  bio_corta: string | null
  especialidades: string[]
  color_agenda: string
  horarios: Record<string, { activo: boolean; inicio: string; fin: string }>
  calificacion_promedio: number
  total_atenciones: number
  activo: boolean
  estado: string
}

export interface Servicio {
  id: string
  nombre: string
  descripcion: string | null
  duracion_minutos: number
  precio: number
  precio_descuento: number | null
  precio_vigente: number
  activo: boolean
  destacado: boolean
  categoria_id: string | null
}

export interface Turno {
  id: string
  cliente_id: string
  trabajador_id: string
  servicio_id: string
  fecha: string
  hora_inicio: string
  hora_fin: string
  estado: 'pendiente' | 'confirmado' | 'cancelado' | 'atendido' | 'ausente' | 'en_curso'
  origen: string
  precio_base: number | null
  precio_final: number | null
  notas_cliente: string | null
  notas_post_servicio: string | null
  cliente_nombre: string | null
  trabajador_nombre: string | null
  servicio_nombre: string | null
  duracion_minutos: number
}

export interface ResumenDashboard {
  periodo: { desde: string; hasta: string; nombre: string }
  facturacion: {
    bruta: number
    neta: number
    comisiones: number
    variacion_pct: number
    ticket_promedio: number
  }
  turnos: {
    total: number
    atendidos: number
    ausentes: number
    cancelados: number
    tasa_ausencia_pct: number
    variacion_pct: number
  }
  clientes: {
    unicos_periodo: number
    nuevos: number
    recurrentes: number
  }
  top: {
    trabajador: { nombre: string; facturacion: number } | null
    servicio: { nombre: string; cantidad: number } | null
  }
  alertas: Array<{ tipo: string; mensaje: string }>
}

export interface BloqueDisponible {
  hora_inicio: string
  hora_fin: string
}

export interface ApiError {
  error: boolean
  codigo: number
  detalle: string
  path: string
}

