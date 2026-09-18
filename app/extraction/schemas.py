from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.schemas.environmental_state import EnvironmentalState


class ExtractionResult(BaseModel):
    raw_input: str
    extracted_state: EnvironmentalState
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction_method: str = Field(default="rule_based")