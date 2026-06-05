"""
main.py — Punto de entrada de la aplicación FastAPI.

Crea la instancia principal de la app, configura CORS,
incluye todos los routers y define el endpoint de health check.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


# ─── Instancia principal de FastAPI ───────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="API REST para gestión de turnos, CRM y automatización WhatsApp",
    version="0.1.0",
    # Swagger UI disponible en /docs — solo en desarrollo
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)


# ─── CORS (Cross-Origin Resource Sharing) ─────────────────────────────────────
# Permite que el frontend (Next.js en puerto 3000) llame a esta API.
# En producción reemplazar por el dominio real.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Next.js en desarrollo
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],          # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
)


# ─── Routers ──────────────────────────────────────────────────────────────────
# Acá se van agregando los routers a medida que los creamos.
# Ejemplo: from app.routers import clientes, turnos, trabajadores
# app.include_router(clientes.router, prefix="/api/v1")


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def root():
    """
    Endpoint raíz — verifica que la API esté funcionando.
    Útil para monitoreo y para verificar el deploy.
    """
    return {
        "app": settings.app_name,
        "status": "ok",
        "version": "0.1.0",
        "env": settings.app_env,
    }


@app.get("/health", tags=["health"])
def health_check():
    """
    Health check detallado para sistemas de monitoreo.
    """
    return {
        "status": "healthy",
        "database": "pending",   # Se actualiza cuando conectemos la DB
    }