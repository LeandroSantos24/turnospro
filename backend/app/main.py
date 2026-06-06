"""
main.py — Punto de entrada de la aplicación FastAPI.

Registra todos los routers y configura CORS, middleware
y manejo global de errores.
"""

import traceback
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.routers import auth, clientes

# ─── Instancia principal ──────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="API REST para gestión de turnos, CRM y automatización WhatsApp",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Manejo global de errores ─────────────────────────────────────────────────

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error":   True,
            "codigo":  exc.status_code,
            "detalle": exc.detail,
            "path":    str(request.url.path),
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errores = []
    for error in exc.errors():
        campo = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
        errores.append({
            "campo":   campo or "general",
            "mensaje": error["msg"].replace("Value error, ", ""),
            "tipo":    error["type"],
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error":   True,
            "codigo":  422,
            "detalle": "Error de validación en los datos enviados",
            "errores": errores,
            "path":    str(request.url.path),
        }
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    detalle = traceback.format_exc() if settings.debug else "Error interno del servidor."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error":   True,
            "codigo":  500,
            "detalle": detalle,
            "path":    str(request.url.path),
        }
    )

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(clientes.router)

# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def root():
    return {
        "app":     settings.app_name,
        "status":  "ok",
        "version": "0.1.0",
        "env":     settings.app_env,
    }

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy"}