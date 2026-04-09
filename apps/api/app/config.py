from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    app_name: str = "HireIQ API"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    database_url: str = "postgresql+asyncpg://hireiq:hireiq@localhost:5432/hireiq"

    # ------------------------------------------------------------------ #
    # Azure AD / Entra ID
    # ------------------------------------------------------------------ #
    azure_ad_tenant_id: str = ""
    azure_ad_client_id: str = ""
    azure_ad_client_secret: str = ""
    azure_ad_authority: str = ""        # https://login.microsoftonline.com/<tenant>
    azure_ad_redirect_uri: str = ""     # https://app.hireiq.io/auth/callback
    azure_ad_scopes: list[str] = ["openid", "profile", "email"]

    # ------------------------------------------------------------------ #
    # Azure Blob Storage
    # ------------------------------------------------------------------ #
    azure_storage_account_name: str = ""
    azure_storage_account_key: str = ""
    azure_storage_connection_string: str = ""
    azure_storage_container_resumes: str = "resumes"
    azure_storage_container_jds: str = "job-descriptions"
    azure_storage_sas_expiry_hours: int = 1

    # ------------------------------------------------------------------ #
    # Stripe
    # ------------------------------------------------------------------ #
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_pro: str = ""           # Pro plan price ID (AUD)
    stripe_price_id_pro_usd: str = ""      # Pro plan price ID (USD)
    stripe_price_id_team: str = ""         # Team plan price ID

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # ------------------------------------------------------------------ #
    # Security / JWT
    # ------------------------------------------------------------------ #
    secret_key: str = "changeme-in-production"
    algorithm: str = "RS256"

    # ------------------------------------------------------------------ #
    # Azure OpenAI
    # ------------------------------------------------------------------ #
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-06-01"
    azure_openai_deployment_mini: str = "gpt-4o-mini"
    azure_openai_deployment_embedding: str = "text-embedding-3-small"

    # ------------------------------------------------------------------ #
    # SMTP (contact form emails)
    # ------------------------------------------------------------------ #
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = "noreply@domato.ai"
    smtp_to: str = "support@domato.ai"

    # ------------------------------------------------------------------ #
    # Plan limits (free tier)
    # ------------------------------------------------------------------ #
    free_tier_max_candidates_per_role: int = 10
    free_tier_max_roles_per_workspace: int = 3
    free_tier_max_workspaces: int = 1

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("azure_ad_scopes", mode="before")
    @classmethod
    def parse_scopes(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (safe for use as a FastAPI dependency)."""
    return Settings()
