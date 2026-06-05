"""Application settings via environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "postgresql+psycopg://mcq:mcq_dev_password@localhost:5432/mcq_platform"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000"

    session_cookie_name: str = "session_id"
    session_cookie_path: str = "/api/v1"
    session_cookie_secure: bool = False
    examiner_session_ttl_seconds: int = 3600
    examinee_session_ttl_seconds: int = 14400
    lockout_max_attempts: int = 5
    lockout_window_seconds: int = 900
    lockout_cooldown_seconds: int = 900
    bcrypt_rounds: int = 12
    problem_type_base_url: str = "https://api.example.com/problems"
    csrf_token_ttl_seconds: int = 3600
    registration_rate_limit_max: int = 10
    registration_rate_limit_window_seconds: int = 3600
    submit_idempotency_ttl_seconds: int = 86400
    min_active_questions: int = 50

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
