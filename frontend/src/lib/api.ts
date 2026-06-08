// lib/api.ts — Cliente HTTP con auto-refresh de JWT

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ─── Instancia principal ──────────────────────────────────────────────────────
const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

// ─── Interceptor de request — agrega el JWT ──────────────────────────────────
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ─── Interceptor de response — auto-refresh en 401 ───────────────────────────
let isRefreshing = false
let pendingRequests: Array<(token: string) => void> = []

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Si no es 401 o ya reintentamos, rechazamos
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error)
    }

    // Si ya estamos refrescando, encolar el request
    if (isRefreshing) {
      return new Promise((resolve) => {
        pendingRequests.push((newToken: string) => {
          original.headers.Authorization = `Bearer ${newToken}`
          resolve(api(original))
        })
      })
    }

    original._retry = true
    isRefreshing = true

    try {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) throw new Error('No refresh token')

      const { data } = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, {
        refresh_token: refreshToken,
      })

      const newToken = data.access_token
      localStorage.setItem('access_token', newToken)
      localStorage.setItem('refresh_token', data.refresh_token)

      // Procesamos los requests pendientes
      pendingRequests.forEach((cb) => cb(newToken))
      pendingRequests = []

      original.headers.Authorization = `Bearer ${newToken}`
      return api(original)
    } catch {
      // Refresh falló — limpiar sesión y redirigir al login
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
      return Promise.reject(error)
    } finally {
      isRefreshing = false
    }
  }
)

export default api

// ─── Helpers tipados por módulo ───────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/api/v1/auth/login', { email, password }),
  me: () => api.get('/api/v1/auth/me'),
  logout: () => api.post('/api/v1/auth/logout'),
}

export const clientesApi = {
  listar: (params?: Record<string, unknown>) =>
    api.get('/api/v1/clientes/', { params }),
  buscar: (q: string) =>
    api.get('/api/v1/clientes/buscar', { params: { q } }),
  obtener: (id: string) =>
    api.get(`/api/v1/clientes/${id}`),
  crear: (data: Record<string, unknown>) =>
    api.post('/api/v1/clientes/', data),
  actualizar: (id: string, data: Record<string, unknown>) =>
    api.patch(`/api/v1/clientes/${id}`, data),
  nota: (id: string, nota: string) =>
    api.post(`/api/v1/clientes/${id}/nota`, null, { params: { nota } }),
}

export const trabajadoresApi = {
  listar: () => api.get('/api/v1/trabajadores/'),
  obtener: (id: string) => api.get(`/api/v1/trabajadores/${id}`),
  disponibilidad: (id: string, fecha: string, duracion: number) =>
    api.get(`/api/v1/trabajadores/${id}/disponibilidad`, {
      params: { fecha, duracion_minutos: duracion },
    }),
}

export const serviciosApi = {
  listar: (params?: Record<string, unknown>) =>
    api.get('/api/v1/servicios/', { params }),
  categorias: () => api.get('/api/v1/servicios/categorias'),
}

export const turnosApi = {
  listar: (params?: Record<string, unknown>) =>
    api.get('/api/v1/turnos/', { params }),
  obtener: (id: string) => api.get(`/api/v1/turnos/${id}`),
  crear: (data: Record<string, unknown>) =>
    api.post('/api/v1/turnos/', data),
  confirmar: (id: string) =>
    api.post(`/api/v1/turnos/${id}/confirmar`),
  cancelar: (id: string, motivo?: string) =>
    api.post(`/api/v1/turnos/${id}/cancelar`, null, { params: { motivo } }),
  atender: (id: string) =>
    api.post(`/api/v1/turnos/${id}/atender`),
  ausente: (id: string) =>
    api.post(`/api/v1/turnos/${id}/ausente`),
  notas: (id: string, notas_post_servicio: string) =>
    api.patch(`/api/v1/turnos/${id}/notas`, { notas_post_servicio }),
}

export const pagosApi = {
  registrar: (data: Record<string, unknown>) =>
    api.post('/api/v1/pagos/', data),
  historial: (params?: Record<string, unknown>) =>
    api.get('/api/v1/pagos/', { params }),
  cierreCaja: (fecha?: string) =>
    api.get('/api/v1/pagos/cierre-caja', { params: { fecha } }),
  comisiones: () => api.get('/api/v1/pagos/comisiones'),
  actualizarComisiones: (data: Record<string, unknown>) =>
    api.put('/api/v1/pagos/comisiones', data),
}

export const estadisticasApi = {
  resumen: (periodo = 'mes') =>
    api.get('/api/v1/estadisticas/resumen', { params: { periodo } }),
  heatmap: (semanas = 8) =>
    api.get('/api/v1/estadisticas/heatmap', { params: { semanas } }),
  facturacion: (periodo = 'mes') =>
    api.get('/api/v1/estadisticas/facturacion', { params: { periodo } }),
  servicios: (periodo = 'mes') =>
    api.get('/api/v1/estadisticas/servicios', { params: { periodo } }),
  trabajadores: (periodo = 'mes') =>
    api.get('/api/v1/estadisticas/trabajadores', { params: { periodo } }),
  clientes: (periodo = 'mes') =>
    api.get('/api/v1/estadisticas/clientes', { params: { periodo } }),
}