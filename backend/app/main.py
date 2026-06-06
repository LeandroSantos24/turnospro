"""
main.py — Punto de entrada de la aplicación FastAPI.

Incluye manejo global de errores para todos los casos posibles:
  - 400 Bad Request
  - 401 Unauthorized
  - 403 Forbidden
  - 404 Not Found
  - 422 Validation Error
  - 429 Rate Limit
  - 500 Internal Server Error
"""

import traceback
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.routers import auth


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
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Manejo global de errores ─────────────────────────────────────────────────

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Captura todos los HTTPException y los devuelve en formato estándar.
    Incluye el path del request para facilitar el debugging.
    """
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
    """
    Captura errores de validación de Pydantic (422).
    Los formatea de forma legible para el frontend.

    En vez de devolver el error técnico de Pydantic,
    devolvemos mensajes legibles por campo.
    """
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
    """
    Captura cualquier error no manejado (500).
    En producción: loguea el error y devuelve mensaje genérico.
    En desarrollo: devuelve el traceback completo para debugging.
    """
    # En producción NUNCA mostrar el traceback al cliente
    if settings.debug:
        detalle = traceback.format_exc()
    else:
        detalle = "Error interno del servidor. Nuestro equipo fue notificado."
        # TODO: Integrar con Sentry cuando vayamos a producción
        # sentry_sdk.capture_exception(exc)

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