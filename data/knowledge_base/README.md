# Knowledge Base — Adding Real Scientific Documents

This directory holds the **real** scientific/authoritative source documents
that back every recommendation the system makes (FAO, IPCC, UNEP, IPBES,
peer-reviewed literature, government reports, etc.).

**No documents ship here by default.** The ingestion pipeline refuses to
fabricate metadata, so every document must be added by a human who can
vouch for its title, organization, year, and URL. See
`tests/fixtures/sample_documents/` for clearly-labeled synthetic documents
used only to test the pipeline's mechanics (extraction/cleaning/chunking) —
those are never real evidence and must never be treated as such.

## How to add a document

1. Download the source file (PDF, or save as plain text/Markdown) into
   `data/knowledge_base/raw/`. Use a clear filename, e.g.
   `fao-2024-soc-drylands.pdf`.

2. Add an entry to `manifest.json` (a JSON array) with **every** field
   filled in from the real source — do not guess or leave placeholders:

```json
[
  {
    "document_id": "fao-2024-soc-drylands",
    "file": "fao-2024-soc-drylands.pdf",
    "metadata": {
      "title": "Exact title as it appears on the document",
      "source": "Publication series or journal name",
      "organization": "FAO",
      "publication_year": 2024,
      "url": "https://www.fao.org/...",
      "topic": "Soil organic carbon dynamics in dryland cropping systems",
      "environmental_metrics": [
        "soil.organic_carbon_percent",
        "climate.rainfall_mm",
        "land.cropping_system"
      ],
      "geographic_scope": "global drylands",
      "document_type": "report"
    }
  }
]
```

Field notes:

- `document_id`: a stable, unique slug you choose (used as the chunk id prefix).
- `file`: path relative to `data/knowledge_base/raw/`.
- `url`: only include if it's a real, working link to the source. Omit
  (`null`) rather than invent one.
- `environmental_metrics`: tag each document with the `EnvironmentalState`
  fields it's evidentially relevant to (see
  `app/schemas/environmental_state.py`) — this powers metadata-filtered
  retrieval in Phase 5.
- `document_type`: one of `research`, `report`, `government_report`,
  `policy_brief`, `dataset`, `other`.

If any required field is missing or malformed, `scripts/ingest_documents.py`
will fail loudly with a message naming the exact entry and field — it will
never silently proceed with a guessed value.

## Running ingestion

```bash
python scripts/ingest_documents.py
```

This reads `manifest.json`, extracts + cleans + chunks each referenced file,
and writes `data/knowledge_base/processed/chunks.jsonl`. That file is what
Phase 4 (embeddings) consumes to populate ChromaDB — ingestion never talks
to the vector database directly.
