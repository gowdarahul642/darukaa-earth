from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.schemas.environmental_state import EnvironmentalState
from app.db import repository
from app.db.session import init_db


class ConversationMemoryManager:
    """Orchestrates session memory access via functional repository entry points."""

    def __init__(self, db_session: Session):
        init_db()
        self.db = db_session

    def get_or_create_session(self, conversation_id: str | None = None) -> str:
        conv = repository.get_or_create_conversation(self.db, conversation_id)
        self.db.commit()
        return conv.id

    def get_profile(self, conversation_id: str) -> EnvironmentalState:
        return repository.get_profile(self.db, conversation_id)

    def update_profile(
        self, conversation_id: str, new_state: EnvironmentalState
    ) -> EnvironmentalState:
        merged = repository.upsert_profile(self.db, conversation_id, new_state)
        self.db.commit()
        return merged

    def record_evidence_claim(
        self,
        conversation_id: str,
        claim: str,
        source_id: str,
        source_title: str,
        retrieved_chunk: str,
        confidence: str,
        source_url: str | None = None,
    ) -> None:
        repository.log_evidence(
            db=self.db,
            conversation_id=conversation_id,
            claim=claim,
            source_id=source_id,
            source_title=source_title,
            retrieved_chunk=retrieved_chunk,
            confidence=confidence,
            source_url=source_url,
        )
        self.db.commit()

    def get_evidence(self, conversation_id: str) -> List[Dict[str, Any]]:
        records = repository.get_evidence_for_conversation(self.db, conversation_id)
        return [
            {
                "claim": r.claim,
                "source_id": r.source_id,
                "source_title": r.source_title,
                "source_url": r.source_url,
                "retrieved_chunk": r.retrieved_chunk,
                "confidence": r.confidence,
            }
            for r in records
        ]