from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LAB_", env_file=None, extra="ignore")

    service_name: str = "chaos-api"
    chaos_token: str = "change-me"
    otel_enabled: bool = True
    otlp_endpoint: str = "http://otel-collector:4318"

    pg_vector_dsn: str = "postgresql://lab:lab@pgvector:5432/vectors"
    pg_state_dsn: str = "postgresql://lab:lab@postgres-state:5432/agent_state"
    qdrant_url: str = "http://qdrant:6333"

    llm_backend: str = "stub"  # "stub" now; "openai_compat" (vLLM) later
    stub_ttft_s: float = 0.05
    stub_itl_s: float = 0.01


def get_settings() -> Settings:
    return Settings()
