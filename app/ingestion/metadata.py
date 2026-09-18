"""
Document metadata schema and manifest loading.

CRITICAL ANTI-HALLUCINATION RULE (spec sections 5 and 16):
Metadata is NEVER inferred, guessed, or auto-extracted from document content
by this system. Every field below must be supplied explicitly by whoever
adds a document to the knowledge base, in `data/knowledge_base/manifest.json`.
If a required field is missing, `load_manifest()` raises a clear error
identifying exactly which entry and field is missing — it does not fall
back to a default, a placeholder, or a "best guess" from the PDF text.

This is what makes it structurally impossible (not just a prompting
instruction) for a fabricated organization, year, or URL to enter the
knowledge base: the pipeline simply won't ingest a document without real,
human-supplied metadata for every required field.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DocumentType = Literal["research", "report", "government_report", "policy_brief", "dataset", "other"]


class DocumentMetadata(BaseModel):
    """Metadata for one scientific/authoritative source document.

    Field names and semantics match spec section 5 exactly so this can be
    surfaced directly in the frontend's "Sources / Evidence" panel later
    without transformation.
    """

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1, description="Publication venue, e.g. journal name or report series.")
    organization: str = Field(..., min_length=1, description="e.g. 'FAO', 'IPCC', 'UNEP', 'IPBES', a university.")
    publication_year: int = Field(..., ge=1900, le=2100)
    url: str | None = Field(default=None, description="Only set if a real, verifiable URL exists. Never fabricated.")
    topic: str = Field(..., min_length=1, description="e.g. 'soil organic carbon and drought resilience'.")
    environmental_metrics: list[str] = Field(
        ...,
        min_length=1,
        description="Tags matching EnvironmentalState field names where possible, "
        "e.g. ['soil.organic_carbon_percent', 'climate.rainfall_mm']. Used for "
        "metadata-filtered retrieval in Phase 5.",
    )
    geographic_scope: str = Field(..., min_length=1, description="e.g. 'global', 'sub-Saharan Africa', 'India'.")
    document_type: DocumentType

    @field_validator("url")
    @classmethod
    def _url_looks_like_a_url(cls, v: str | None) -> str | None:
        if v is not None and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("url must start with http:// or https:// if provided")
        return v


class ManifestEntry(BaseModel):
    """One row in manifest.json: a document's metadata plus where to find its
    source file on disk."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(..., min_length=1, description="Stable unique slug, e.g. 'fao-2024-soc-drylands'.")
    file: str = Field(..., min_length=1, description="Path relative to data/knowledge_base/raw/.")
    metadata: DocumentMetadata


class ManifestError(ValueError):
    """Raised when manifest.json is malformed or a required field is missing.

    Deliberately a distinct exception type so callers (CLI, tests) can
    distinguish "your manifest is invalid" from other errors, and so the
    error message can point at exactly which entry/field is the problem.
    """


def load_manifest(manifest_path: Path) -> list[ManifestEntry]:
    """Load and validate manifest.json. Raises ManifestError with a specific,
    actionable message if any entry is missing required metadata — never
    silently skips or fills in a guessed value.
    """
    if not manifest_path.exists():
        raise ManifestError(f"Manifest not found at {manifest_path}")

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ManifestError(f"Manifest at {manifest_path} is not valid JSON: {e}") from e

    if not isinstance(raw, list):
        raise ManifestError(f"Manifest at {manifest_path} must be a JSON array of document entries.")

    entries: list[ManifestEntry] = []
    seen_ids: set[str] = set()
    for i, item in enumerate(raw):
        try:
            entry = ManifestEntry.model_validate(item)
        except Exception as e:
            title_hint = item.get("document_id", f"index {i}") if isinstance(item, dict) else f"index {i}"
            raise ManifestError(f"Manifest entry '{title_hint}' is invalid: {e}") from e
        if entry.document_id in seen_ids:
            raise ManifestError(f"Duplicate document_id '{entry.document_id}' in manifest.")
        seen_ids.add(entry.document_id)
        entries.append(entry)

    return entries
