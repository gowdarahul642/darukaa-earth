"""
Repository layer: the only place that translates between
`EnvironmentalState` (Pydantic, used everywhere in business logic) and the
SQLAlchemy ORM rows (used only for persistence).
"""

from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models import Conversation, EnvironmentalProfile, EvidenceLog
from app.schemas.environmental_state import EnvironmentalState


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------


def create_conversation(db: Session) -> Conversation:
    conversation = Conversation()
    db.add(conversation)
    db.flush()
    return conversation


def get_conversation(db: Session, conversation_id: str) -> Conversation | None:
    return db.get(Conversation, conversation_id)


def get_or_create_conversation(db: Session, conversation_id: str | None) -> Conversation:
    """Look up a conversation by id; create a new one if id is None or unknown."""
    if conversation_id:
        existing = get_conversation(db, conversation_id)
        if existing is not None:
            return existing
    return create_conversation(db)


# ---------------------------------------------------------------------------
# Environmental profiles (conversation memory)
# ---------------------------------------------------------------------------


def get_profile(db: Session, conversation_id: str) -> EnvironmentalState:
    """Return the current EnvironmentalState for a conversation."""
    row = db.query(EnvironmentalProfile).filter_by(conversation_id=conversation_id).one_or_none()
    if row is None:
        return EnvironmentalState()
    return EnvironmentalState.model_validate(row.state_json)


def save_profile(db: Session, conversation_id: str, state: EnvironmentalState) -> EnvironmentalProfile:
    """Overwrite the stored profile for a conversation with state exactly as given."""
    row = db.query(EnvironmentalProfile).filter_by(conversation_id=conversation_id).one_or_none()
    payload = state.model_dump(mode="json")
    if row is None:
        row = EnvironmentalProfile(
            conversation_id=conversation_id,
            region=state.region,
            latitude=state.latitude,
            longitude=state.longitude,
            state_json=payload,
        )
        db.add(row)
    else:
        row.region = state.region
        row.latitude = state.latitude
        row.longitude = state.longitude
        row.state_json = payload
    db.flush()
    return row


def upsert_profile(db: Session, conversation_id: str, new_state: EnvironmentalState) -> EnvironmentalState:
    """Merge new_state into whatever is already known for this conversation and persist."""
    existing = get_profile(db, conversation_id)
    merged = existing.merge(new_state)
    save_profile(db, conversation_id, merged)
    return merged


# ---------------------------------------------------------------------------
# Evidence traceability
# ---------------------------------------------------------------------------


def log_evidence(
    db: Session,
    conversation_id: str,
    claim: str,
    source_id: str,
    source_title: str,
    retrieved_chunk: str,
    confidence: str,
    source_url: str | None = None,
) -> EvidenceLog:
    """Record that claim was supported by a specific retrieved chunk."""
    row = EvidenceLog(
        conversation_id=conversation_id,
        claim=claim,
        source_id=source_id,
        source_title=source_title,
        source_url=source_url,
        retrieved_chunk=retrieved_chunk,
        confidence=confidence,
    )
    db.add(row)
    db.flush()
    return row


def get_evidence_for_conversation(db: Session, conversation_id: str) -> list[EvidenceLog]:
    return db.query(EvidenceLog).filter_by(conversation_id=conversation_id).order_by(EvidenceLog.created_at).all()