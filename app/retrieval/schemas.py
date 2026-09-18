from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class RetrievedEvidence(BaseModel):
    chunk_id: str
    content: str
    document_title: str
    organization: str
    publication_year: int
    url: str
    topic: str
    environmental_metrics: List[str]
    similarity_score: float
    query_used: str


class RAGRetrievalResult(BaseModel):
    primary_query: str
    composite_queries: List[str]
    total_retrieved: int
    evidence: List[RetrievedEvidence]