"""Scientific document ingestion pipeline.

    manifest.json -> loaders.py (extract) -> cleaning.py -> chunking.py
    -> schemas.py (IngestedChunk, metadata attached) -> pipeline.py (orchestration)

- metadata.py   : DocumentMetadata + ManifestEntry schemas and manifest.json
                  loader. Enforces that metadata is always human-supplied,
                  never inferred or guessed.
- loaders.py    : raw text extraction from .pdf / .txt / .md.
- cleaning.py   : conservative text normalization (hyphenation, whitespace).
- chunking.py   : whitespace-aware overlapping chunking.
- schemas.py    : IngestedChunk, the self-describing output unit.
- pipeline.py   : orchestrates the above; writes/reads a chunks.jsonl file
                  that Phase 4 (embeddings) consumes without needing to know
                  anything about PDFs or manifests.
"""
