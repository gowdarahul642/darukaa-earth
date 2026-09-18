"""
Phase 2 tests: SQLite persistence layer.

Each test gets an isolated, temp-file-backed database by resetting the
cached engine/session factory and pointing app.config's cached Settings at
a temp path. This avoids tests polluting each other or the real dev DB.
"""

import pytest

from app.config import get_settings
from app.db import repository as repo
from app.db.session import get_session, init_db, reset_engine_for_testing
from app.schemas import EnvironmentalState, SoilState


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Point the app at a fresh temp SQLite file for every test."""
    get_settings.cache_clear()
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("KNOWLEDGE_BASE_DIR", str(tmp_path / "kb"))
    reset_engine_for_testing()
    init_db()
    yield
    reset_engine_for_testing()
    get_settings.cache_clear()


def test_create_and_fetch_conversation():
    with get_session() as db:
        conv = repo.create_conversation(db)
        conv_id = conv.id

    with get_session() as db:
        fetched = repo.get_conversation(db, conv_id)
        assert fetched is not None
        assert fetched.id == conv_id


def test_get_or_create_conversation_creates_when_unknown():
    with get_session() as db:
        conv = repo.get_or_create_conversation(db, conversation_id=None)
        assert conv.id is not None


def test_get_or_create_conversation_reuses_known_id():
    with get_session() as db:
        conv = repo.create_conversation(db)
        conv_id = conv.id

    with get_session() as db:
        same = repo.get_or_create_conversation(db, conv_id)
        assert same.id == conv_id


def test_empty_profile_for_unknown_conversation():
    with get_session() as db:
        conv = repo.create_conversation(db)
        state = repo.get_profile(db, conv.id)
        assert state.is_empty()


def test_upsert_profile_persists_and_round_trips():
    with get_session() as db:
        conv = repo.create_conversation(db)
        conv_id = conv.id
        new_state = EnvironmentalState(region="semi-arid", soil=SoilState(organic_carbon_percent=0.3))
        merged = repo.upsert_profile(db, conv_id, new_state)
        assert merged.region == "semi-arid"

    # Fresh session: confirm it was actually persisted, not just in-memory
    with get_session() as db:
        reloaded = repo.get_profile(db, conv_id)
        assert reloaded.region == "semi-arid"
        assert reloaded.soil.organic_carbon_percent == 0.3


def test_upsert_profile_merges_across_multiple_turns():
    """Simulates a multi-turn conversation: turn 1 provides SOC + rainfall,
    turn 2 provides land use — final profile must contain all of it."""
    with get_session() as db:
        conv = repo.create_conversation(db)
        conv_id = conv.id

    turn_1 = EnvironmentalState(
        soil=SoilState(organic_carbon_percent=0.3),
        climate={"rainfall_category": "low"},
    )
    with get_session() as db:
        repo.upsert_profile(db, conv_id, turn_1)

    turn_2 = EnvironmentalState(land={"crop_type": "wheat", "cropping_system": "monoculture"})
    with get_session() as db:
        final_state = repo.upsert_profile(db, conv_id, turn_2)

    assert final_state.soil.organic_carbon_percent == 0.3
    assert final_state.climate.rainfall_category == "low"
    assert final_state.land.crop_type == "wheat"
    assert final_state.land.cropping_system == "monoculture"


def test_evidence_log_round_trip():
    with get_session() as db:
        conv = repo.create_conversation(db)
        conv_id = conv.id
        repo.log_evidence(
            db,
            conversation_id=conv_id,
            claim="Legume cover crops can increase soil organic carbon inputs.",
            source_id="fao-2024-soc-report",
            source_title="Soil Organic Carbon in Agricultural Systems",
            retrieved_chunk="Cover cropping with legumes has been shown to increase organic matter inputs...",
            confidence="medium",
            source_url="https://example.org/fao-soc-report",
        )

    with get_session() as db:
        logs = repo.get_evidence_for_conversation(db, conv_id)
        assert len(logs) == 1
        assert logs[0].source_id == "fao-2024-soc-report"
        assert logs[0].confidence == "medium"


def test_evidence_logs_scoped_to_conversation():
    with get_session() as db:
        conv_a = repo.create_conversation(db)
        conv_b = repo.create_conversation(db)
        conv_a_id, conv_b_id = conv_a.id, conv_b.id
        repo.log_evidence(
            db, conv_a_id, "claim A", "src-a", "Title A", "chunk A", "high"
        )
        repo.log_evidence(
            db, conv_b_id, "claim B", "src-b", "Title B", "chunk B", "low"
        )

    with get_session() as db:
        logs_a = repo.get_evidence_for_conversation(db, conv_a_id)
        assert len(logs_a) == 1
        assert logs_a[0].source_id == "src-a"
