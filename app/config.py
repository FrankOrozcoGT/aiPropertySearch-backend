"""Application Configuration - Environment variables and settings"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses pydantic-settings for validation and type safety.
    """

    # App Settings
    APP_NAME: str = "PropTech API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database Settings
    DB_HOST: str = "mysql"
    DB_PORT: int = 3306
    DB_USER: str = "appuser"
    DB_PASSWORD: str = "apppass"
    DB_NAME: str = "propiedades_db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # LLM Settings (Ollama)
    OLLAMA_URL: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_TIMEOUT: int = 30  # seconds

    # API Settings
    CORS_ORIGINS: str = "*"
    API_PREFIX: str = "/api"

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton settings instance
settings = Settings()
