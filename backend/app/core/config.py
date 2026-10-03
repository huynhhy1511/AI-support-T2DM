from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI-support-T2DM"
    app_env: str = "development"
    database_url: str = (
        "postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/diabetes_ai_dev"
    )
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
