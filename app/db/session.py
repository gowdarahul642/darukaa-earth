"""
Database engine and session management.

Single SQLite file, path controlled entirely by `app.config.Settings`
(`SQLITE_PATH` env var). No other module should construct an engine or
session directly — use `get_session()` (plain context manager) or
`get_db()` (FastAPI dependency, added when routers exist in Phase 12).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db.models import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        settings.ensure_directories()
        _engine = create_engine(
            f"sqlite:///{settings.sqlite_path}",
            connect_args={"check_same_thread": False},
        )
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal


def init_db() -> None:
    """Create all tables if they don't already exist. Safe to call repeatedly."""
    Base.metadata.create_all(bind=get_engine())


@contextmanager
def get_session() -> Iterator[Session]:
    """Context-managed session for use outside of FastAPI request handlers
    (scripts, tests, ingestion jobs)."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency version of get_session(). Wired into routers in Phase 12."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine_for_testing() -> None:
    """Drop the cached engine/session factory so tests can point at a fresh
    (e.g. in-memory or temp-file) database via a different settings instance.
    Not used in production code paths."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
