"""
database.py — Configuración de la base de datos.

Establece la conexión con PostgreSQL usando SQLAlchemy.
Define el motor (engine), la sesión y la clase Base
que heredan todos los modelos del sistema.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings


# ─── Motor de base de datos ────────────────────────────────────────────────────
# El engine es el punto de conexión con PostgreSQL.
# pool_pre_ping=True verifica que la conexión siga activa antes de usarla.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug,  # Si debug=True, imprime todas las queries SQL en consola
)


# ─── Fábrica de sesiones ───────────────────────────────────────────────────────
# Cada request HTTP recibe su propia sesión de base de datos.
# autocommit=False: los cambios no se guardan solos, hay que hacer commit()
# autoflush=False: no envía cambios a la DB hasta que se haga commit()
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ─── Clase Base para modelos ───────────────────────────────────────────────────
# Todos los modelos (Cliente, Turno, Trabajador, etc.) heredan de esta Base.
# SQLAlchemy la usa para saber qué tablas existen y cómo están definidas.
Base = declarative_base()


# ─── Dependencia de sesión ─────────────────────────────────────────────────────
def get_db():
    """
    Generador que provee una sesión de base de datos por cada request.

    Uso en FastAPI:
        @router.get("/clientes")
        def get_clientes(db: Session = Depends(get_db)):
            ...

    El bloque try/finally garantiza que la sesión siempre se cierra,
    incluso si ocurre un error durante el request.
    """
    db = SessionLocal()
    try:
        yield db       # Entrega la sesión al endpoint
    finally:
        db.close()     # Cierra la sesión al terminar el request