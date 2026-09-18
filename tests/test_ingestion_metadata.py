"""
Phase 3 tests: DocumentMetadata validation and manifest.json loading.

These tests specifically verify the anti-hallucination guarantee: a
document with missing or malformed required metadata must be rejected, not
silently accepted with a guessed/default value.
"""

import json

import pytest

from app.ingestion.metadata import DocumentMetadata, ManifestError, load_manifest


def _valid_metadata_dict():
    return {
        "title": "Example Report",
        "source": "Example Series",
        "organization": "FAO",
        "publication_year": 2024,
        "url": "https://example.org/report",
        "topic": "soil organic carbon",
        "environmental_metrics": ["soil.organic_carbon_percent"],
        "geographic_scope": "global",
        "document_type": "report",
    }


def test_valid_metadata_constructs():
    meta = DocumentMetadata.model_validate(_valid_metadata_dict())
    assert meta.organization == "FAO"


def test_missing_required_field_rejected():
    data = _valid_metadata_dict()
    del data["organization"]
    with pytest.raises(Exception):
        DocumentMetadata.model_validate(data)


def test_empty_environmental_metrics_rejected():
    data = _valid_metadata_dict()
    data["environmental_metrics"] = []
    with pytest.raises(Exception):
        DocumentMetadata.model_validate(data)


def test_invalid_document_type_rejected():
    data = _valid_metadata_dict()
    data["document_type"] = "blog_post"
    with pytest.raises(Exception):
        DocumentMetadata.model_validate(data)


def test_malformed_url_rejected():
    data = _valid_metadata_dict()
    data["url"] = "not-a-url"
    with pytest.raises(Exception):
        DocumentMetadata.model_validate(data)


def test_url_can_be_omitted():
    data = _valid_metadata_dict()
    data["url"] = None
    meta = DocumentMetadata.model_validate(data)
    assert meta.url is None


def test_unknown_field_rejected():
    """extra='forbid' — no accidental or invented fields slip through."""
    data = _valid_metadata_dict()
    data["fabricated_confidence_score"] = 0.99
    with pytest.raises(Exception):
        DocumentMetadata.model_validate(data)


# --- Manifest loading ---


def test_load_manifest_missing_file_raises(tmp_path):
    with pytest.raises(ManifestError):
        load_manifest(tmp_path / "does_not_exist.json")


def test_load_manifest_invalid_json_raises(tmp_path):
    p = tmp_path / "manifest.json"
    p.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ManifestError):
        load_manifest(p)


def test_load_manifest_must_be_a_list(tmp_path):
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
    with pytest.raises(ManifestError):
        load_manifest(p)


def test_load_manifest_rejects_entry_with_missing_metadata_field(tmp_path):
    bad_entry = {
        "document_id": "doc-1",
        "file": "doc1.txt",
        "metadata": {**_valid_metadata_dict()},
    }
    del bad_entry["metadata"]["publication_year"]
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps([bad_entry]), encoding="utf-8")
    with pytest.raises(ManifestError, match="doc-1"):
        load_manifest(p)


def test_load_manifest_rejects_duplicate_document_ids(tmp_path):
    entry = {"document_id": "dup", "file": "a.txt", "metadata": _valid_metadata_dict()}
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps([entry, entry]), encoding="utf-8")
    with pytest.raises(ManifestError, match="Duplicate"):
        load_manifest(p)


def test_load_manifest_accepts_valid_multi_entry_manifest(tmp_path):
    entries = [
        {"document_id": "doc-a", "file": "a.txt", "metadata": _valid_metadata_dict()},
        {"document_id": "doc-b", "file": "b.pdf", "metadata": _valid_metadata_dict()},
    ]
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(entries), encoding="utf-8")
    loaded = load_manifest(p)
    assert len(loaded) == 2
    assert {e.document_id for e in loaded} == {"doc-a", "doc-b"}
