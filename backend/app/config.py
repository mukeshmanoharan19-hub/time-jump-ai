from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:root@localhost:5433/timejump"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    cors_origins: str = "http://localhost:3000"
    app_secret_key: str = "change-me-in-production"
    session_ttl_hours: int = 24

    azure_ad_tenant_id: str = ""
    azure_ad_client_id: str = ""
    azure_ad_client_secret: str = ""
    azure_ad_redirect_uri: str = "http://localhost:3000/auth/callback"
    graph_base_url: str = "https://graph.microsoft.com/v1.0"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
