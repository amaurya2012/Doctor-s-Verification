"""
Application configuration.

Loaded from environment variables via pydantic-settings. Includes
production safety guardrails: the app refuses to boot in production
with a default secret key, a SQLite database, or empty CORS origins.
"""
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Environment
    ENVIRONMENT: str = "development"  # development | staging | production

    # App
    PROJECT_NAME: str = "DoctorVerify India"
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: str = "sqlite:///./doctorverify.db"

    # CORS
    CORS_ORIGINS: List[str] = []

    # Google OAuth (optional -- /auth/google simply won't work if unset)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Cloudinary (image uploads; optional)
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Email (verification; optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@doctorverify.in"

    # Uploads
    MAX_UPLOAD_SIZE_MB: int = 5

    @field_validator("ENVIRONMENT")
    @classmethod
    def normalize_env(cls, v: str) -> str:
        return v.lower()

    @property
    def sqlalchemy_database_url(self) -> str:
        """
        DATABASE_URL normalized for SQLAlchemy. Providers (Neon, Heroku,
        Supabase) hand out plain `postgres://` / `postgresql://` URLs, but
        recent SQLAlchemy resolves a bare `postgresql://` to the psycopg v3
        driver. We ship psycopg2, so pin the driver explicitly.
        """
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg2://" + url[len("postgresql://"):]
        return url

    def validate_production_safety(self) -> None:
        """
        Refuse to boot in production with unsafe defaults. Only checks
        things that are genuinely unsafe to run with -- an unset
        Google Client ID just means Google sign-in is disabled, not a
        security hole, so it's intentionally NOT checked here.
        """
        if self.ENVIRONMENT != "production":
            return

        errors = []
        if self.SECRET_KEY == "dev-secret-key-change-me":
            errors.append("SECRET_KEY is still the default dev value")
        if self.DATABASE_URL.startswith("sqlite"):
            errors.append("DATABASE_URL points at SQLite, not a production DB")
        if not self.CORS_ORIGINS:
            errors.append("CORS_ORIGINS is empty")

        if errors:
            raise RuntimeError(
                "Refusing to start in production with unsafe config:\n  - "
                + "\n  - ".join(errors)
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
