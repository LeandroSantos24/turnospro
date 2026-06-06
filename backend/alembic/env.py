"""
alembic/env.py — Configuración del entorno de migraciones.

Conecta Alembic con nuestra base de datos y modelos SQLAlchemy.
Cuando corremos 'alembic revision --autogenerate', Alembic compara
los modelos definidos en app/models/ con el estado actual de la DB
y genera automáticamente el SQL de migración.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Importamos la Base y todos los modelos para que Alembic los detecte
from app.database import Base
from app.config import settings

# Importar modelos acá a medida que los creamos
import app.models  # Carga todos los modelos en Base.metadata
# from app.models.usuario import Usuario

# ─── Configuración de Alembic ─────────────────────────────────────────────────
config = context.config

# Sobrescribimos la URL con la de nuestro .env
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Le decimos a Alembic qué metadata usar para autogenerar migraciones
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Corre migraciones sin conexión activa a la DB (genera SQL puro)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Corre migraciones con conexión activa a la DB (modo normal)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()