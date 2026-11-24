"""Application settings for SELPH.

Hybrid history retrieval settings (ADR-002) are included with sensible defaults.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Hybrid short-term memory (ADR-002)
    hybrid_history_pool_size: int = 20
    hybrid_history_top_k: int = 5
    hybrid_history_recency_weight: float = 0.7
    hybrid_history_overlap_weight: float = 0.3
    hybrid_history_use_time_based_recency: bool = False
    hybrid_history_recency_half_life_days: float = 7.0
    hybrid_history_min_score: float = 0.0
    hybrid_history_prompt_max_chars: int = 0  # 0 = unlimited
    hybrid_history_diversity_threshold: float = 0.0  # 0 = disabled
    hybrid_history_cross_channel: bool = False
    hybrid_history_line_max_chars: int = 300
    hybrid_history_include_subject: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
