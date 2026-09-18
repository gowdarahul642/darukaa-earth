import pytest
from app.db.session import init_db, get_session_factory
from app.schemas.environmental_state import EnvironmentalState, SoilState, LandState
from app.memory.manager import ConversationMemoryManager


@pytest.fixture
def db_session():
    init_db()
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_consecutive_turns_state_merging(db_session):
    memory = ConversationMemoryManager(db_session)
    conversation_id = memory.get_or_create_session()

    # Turn 1
    state_turn1 = memory.update_profile(
        conversation_id,
        EnvironmentalState(region="semi-arid", land=LandState(crop_type="wheat")),
    )
    assert state_turn1.region == "semi-arid"
    assert state_turn1.land.crop_type == "wheat"

    # Turn 2: Incremental state delta
    state_turn2 = memory.update_profile(
        conversation_id,
        EnvironmentalState(soil=SoilState(organic_carbon_percent=0.3)),
    )

    # Assert cumulative profile state
    assert state_turn2.region == "semi-arid"
    assert state_turn2.land.crop_type == "wheat"
    assert state_turn2.soil.organic_carbon_percent == 0.3


def test_evidence_traceability_logging(db_session):
    memory = ConversationMemoryManager(db_session)
    conversation_id = memory.get_or_create_session()

    memory.record_evidence_claim(
        conversation_id=conversation_id,
        claim="Legume cover crop increases SOC in semi-arid wheat systems.",
        source_id="arxiv_2401_1234",
        source_title="Soil Organic Carbon and Ecological Restoration",
        retrieved_chunk="Legume cover cropping significantly increases soil organic carbon...",
        confidence="High",
        source_url="https://arxiv.org/abs/2401.1234",
    )

    retrieved = memory.get_evidence(conversation_id)

    assert len(retrieved) == 1
    assert retrieved[0]["source_id"] == "arxiv_2401_1234"
    assert "Legume" in retrieved[0]["claim"]