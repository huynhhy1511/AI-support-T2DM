from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI-support-T2DM"
    app_env: str = "development"
    database_url: str = (
        "postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/diabetes_ai_dev"
    )
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 30
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
