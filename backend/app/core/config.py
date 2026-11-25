from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "AI-support-T2DM"
    app_env: str = "development"
    database_url: str = (
        "postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/diabetes_ai_dev"
    )
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / "backend" / ".env", BASE_DIR / ".env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
