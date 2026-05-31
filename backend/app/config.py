from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql://astraeus:astraeus_dev@localhost/astraeus"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REFRESH_DAYS: int = 30
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    APP_VERSION: str = "1.0.0"

    DO_SPACES_KEY: str = ""
    DO_SPACES_SECRET: str = ""
    DO_SPACES_BUCKET: str = "astraeus-media"
    DO_SPACES_ENDPOINT: str = "https://nyc3.digitaloceanspaces.com"
    DO_SPACES_REGION: str = "nyc3"


settings = Settings()
