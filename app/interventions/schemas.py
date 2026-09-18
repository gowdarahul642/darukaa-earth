from typing import List, Optional
from pydantic import BaseModel, Field


class ScientificEvidenceCitation(BaseModel):
    title: str
    organization: str
    publication_year: int
    url: str


class RecommendedAction(BaseModel):
    action: str
    why_it_works: str
    environmental_mechanism: str
    metrics_affected: List[str]
    time_horizon: str  # Short (1 season), Medium (2-3 yrs), Long (5+ yrs)
    evidence: List[ScientificEvidenceCitation]
    confidence: str  # High, Medium, Low
    confidence_rationale: str
    trade_offs: List[str]
    monitoring: List[str]