"""
Centralized configuration for DARUKAA.EARTH.

All environment-dependent values (paths, model names, provider choice,
retrieval parameters) live here and ONLY here. No other module should
read os.environ directly. This is what lets later phases swap the LLM,
the embedding model, or storage paths without touching business logic.

Configuration is loaded from environment variables / a `.env` file via
pydantic-settings. See `.env.example` for the full list of supported
variables and their defaults.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = two levels up from this file (app/config.py -> app/ -> root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application-wide settings, sourced from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- General ---
    app_name: str = "darukaa-earth"
    environment: str = Field(default="development", description="development|production|test")
    log_level: str = Field(default="INFO")

    # --- API server ---
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    # --- Storage paths ---
    data_dir: Path = Field(default=PROJECT_ROOT / "data")
    sqlite_path: Path = Field(default=PROJECT_ROOT / "data" / "darukaa.db")
    chroma_persist_dir: Path = Field(default=PROJECT_ROOT / "data" / "chroma")
    knowledge_base_dir: Path = Field(default=PROJECT_ROOT / "data" / "knowledge_base")

    # --- Embeddings (Phase 4) ---
    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Any sentence-transformers-compatible model name.",
    )
    embedding_chunk_size: int = Field(default=800, description="Characters per chunk.")
    embedding_chunk_overlap: int = Field(default=150, description="Character overlap between chunks.")

    # --- Retrieval (Phase 5) ---
    retrieval_top_k: int = Field(default=6)
    retrieval_score_threshold: float = Field(
        default=0.0,
        description="Minimum similarity score to keep a retrieved chunk. 0 disables filtering.",
    )

    # --- LLM (Phase 10) ---
    llm_provider: str = Field(
        default="ollama",
        description="ollama|local_gemma|anthropic|openai|mock (mock used for tests / no-GPU demo mode)",
    )
    llm_model_name: str = Field(
        default="gemma:2b",
        description="Ollama model tag name.",
    )
    llm_base_url: str = Field(
        default="http://127.0.0.1:11434",
        description="Explicit IPv4 loopback address to avoid Windows IPv6 resolution timeouts.",
    )
    llm_api_key: str = Field(default="", description="Only used by hosted providers. Never hard-code.")
    llm_max_new_tokens: int = Field(default=512)
    llm_temperature: float = Field(default=0.2)

    # --- Geo-spatial enrichment (Phase 13 groundwork) ---
    enable_geo_enrichment: bool = Field(
        default=False,
        description="If False, the system explicitly states geographic enrichment is unavailable "
        "instead of fabricating spatial data.",
    )

    def ensure_directories(self) -> None:
        """Create data directories if they don't exist yet. Safe to call repeatedly."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance. Use this everywhere instead of Settings()."""
    s = Settings()
    s.ensure_directories()
    return s


# Module-level instance export to prevent ImportError across Phase 4 modules
settings = get_settings()