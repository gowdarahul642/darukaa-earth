"""
Phase 1 tests: configuration loading.

These tests confirm that Settings() loads with sane defaults even when no
.env file is present, that it is environment-overridable, and that
directory creation is idempotent and safe.
"""

from pathlib import Path

from app.config import Settings, get_settings


def test_settings_load_with_defaults(monkeypatch, tmp_path):
    """Settings should load without requiring a .env file present."""
    monkeypatch.chdir(tmp_path)
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.app_name == "darukaa-earth"
    assert settings.llm_provider in {"local_gemma", "ollama", "anthropic", "openai", "mock"}


def test_settings_env_override(monkeypatch):
    """Environment variables should override defaults."""
    monkeypatch.setenv("APP_NAME", "test-app")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.app_name == "test-app"
    assert settings.llm_provider == "mock"


def test_get_settings_is_cached():
    """get_settings() must return the same instance (used app-wide)."""
    assert get_settings() is get_settings()


def test_ensure_directories_creates_paths(tmp_path):
    """ensure_directories() must create all required data directories."""
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        data_dir=tmp_path / "data",
        chroma_persist_dir=tmp_path / "data" / "chroma",
        knowledge_base_dir=tmp_path / "data" / "knowledge_base",
        sqlite_path=tmp_path / "data" / "darukaa.db",
    )
    settings.ensure_directories()

    assert Path(settings.data_dir).is_dir()
    assert Path(settings.chroma_persist_dir).is_dir()
    assert Path(settings.knowledge_base_dir).is_dir()
    assert Path(settings.sqlite_path.parent).is_dir()
