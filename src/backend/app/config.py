"""
Configuration and settings for SELPH Backend
"""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # Application
    environment: str = "development"
    debug: bool = False
    service_name: str = "selph-backend"
    
    # API
    api_title: str = "SELPH API"
    api_version: str = "0.1.0"
    api_v1_str: str = "/v1"
    
    # Database
    database_url: str = "postgresql://localhost/selph"
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    jwt_refresh_expiration_days: int = 7
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8081",
    ]
    allowed_hosts: List[str] = ["localhost", "127.0.0.1", "testserver"]
    
    # LLM Configuration
    default_llm_provider: str = "anthropic"
    default_llm_model: str = "claude-sonnet-4-6"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    
    # Firebase
    firebase_project_id: str = ""
    firebase_private_key: str = ""
    firebase_client_email: str = ""
    
    # Cloudflare R2
    cloudflare_account_id: str = ""
    cloudflare_r2_access_key_id: str = ""
    cloudflare_r2_secret_access_key: str = ""
    cloudflare_r2_bucket_name: str = "selph-media"
    cloudflare_r2_endpoint: str = ""
    
    # Meta (Instagram)
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_verify_token: str = ""
    meta_oauth_redirect_uri: str = ""  # e.g. https://api.selph.ai/v1/channels/instagram/callback
    
    # Google (Gmail)
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = ""  # e.g. https://api.selph.ai/v1/channels/gmail/callback
    google_pubsub_topic: str = ""  # e.g. projects/selph/topics/gmail-push
    google_webhook_secret: str = ""  # Optional shared secret for /channels/gmail/webhook

    # Voice Clone (Phase 6)
    voice_provider: str = "mock"  # mock | elevenlabs
    elevenlabs_api_key: str = ""
    voice_default_model_id: str = ""
    
    # Logging
    log_level: str = "INFO"
    enable_metrics: bool = True

    # Security hardening
    auth_rate_limit_per_minute: int = 20
    enforce_production_jwt_secret: bool = True
    
    # Feature Flags
    feature_twin_briefing: bool = False
    feature_twin_llm_drafts: bool = False
    feature_twin_llm_json_retry: bool = True
    feature_vip_override: bool = False
    feature_batch_approval: bool = False
    feature_voice_clone: bool = False
    feature_avatar_clone: bool = False
    feature_instagram: bool = False
    feature_gmail: bool = False
    feature_twitter: bool = False
    feature_whatsapp: bool = False

    # Twin LLM Runtime
    twin_llm_max_tokens: int = 600
    twin_llm_temperature: float = 0.7
    twin_llm_timeout_seconds: int = 30
    
    # Moderation
    moderation_threshold: float = 0.7
    strict_moderation: bool = True
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_time_limit: int = 300
    celery_task_soft_time_limit: int = 250
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()


# Backward-compatible module-level settings import target.
settings = get_settings()
