from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.schemas.environmental_state import EnvironmentalState


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    intent_type: str  # "greeting" or "assessment"
    response: str
    environmental_state: EnvironmentalState
    is_sufficient: bool
    missing_fields: List[str]
    vulnerability_scores: Dict[str, float]  # Scores for Radar Chart
    evidence_count: int


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str