from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator


class DocumentMetadata(BaseModel):
    title: str = Field(..., min_length=3, description="Title of the publication or report")
    source: str = Field(..., description="Source journal, organization, or report series name")
    organization: str = Field(..., description="Authoritative organization (e.g., FAO, IPCC, IPBES, UNEP, arXiv)")
    publication_year: int = Field(..., ge=1900, le=2030, description="Year of publication")
    url: Optional[str] = Field(default="", description="Verifiable URL or URI to source document")
    topic: str = Field(..., description="Primary ecological topic covered")
    environmental_metrics: List[str] = Field(
        default_factory=list, 
        description="Target metrics covered (e.g., soil_organic_carbon, rainfall, species_richness)"
    )
    geographic_scope: str = Field(default="Global", description="Geographic applicability")
    document_type: Literal["research", "report", "policy", "case_study"] = Field(
        default="report", description="Type of document source"
    )

    @field_validator("organization", "title")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("Field cannot be empty or whitespace only")
        return v_clean


class DocumentChunk(BaseModel):
    chunk_id: str = Field(..., description="Deterministic unique identifier (doc_hash_idx)")
    document_title: str
    chunk_index: int
    content: str = Field(..., min_length=10, description="Cleaned text content")
    char_count: int
    metadata: DocumentMetadata


class IngestionResult(BaseModel):
    document_title: str
    total_pages: int
    total_chunks: int
    status: Literal["success", "failed", "partial"]
    error: Optional[str] = None