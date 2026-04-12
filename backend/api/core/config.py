"""Configurazione backend SISMASENS tramite variabili d'ambiente."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://sismasens:sismasens@postgres:5432/sismasens"

    # JWT
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 giorni

    # MQTT token (separato dal JWT di accesso API)
    mqtt_token_secret: str = "change-me-mqtt-secret"

    # CORS
    allowed_origins: list[str] = ["https://sismasens.iotzator.com", "http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
