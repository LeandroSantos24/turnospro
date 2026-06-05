"""
config.py — Configuración central de la aplicación.

Usa Pydantic Settings para leer variables de entorno del archivo .env
y exponerlas de forma tipada en toda la aplicación.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Todas las variables de configuración del sistema.
    Pydantic las lee automáticamente del archivo .env
    """

    # Nombre y entorno de la app
    app_name: str = "TurnosPro"
    app_env: str = "development"
    debug: bool = True

    # Base de datos PostgreSQL
    database_url: str

    # JWT para autenticación
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # WhatsApp Cloud API
    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""

    class Config:
        # Le dice a Pydantic que lea desde el archivo .env
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna la instancia de configuración.
    @lru_cache asegura que solo se crea una vez (patrón singleton).
    """
    return Settings()


# Instancia global para importar en otros módulos
settings = get_settings()