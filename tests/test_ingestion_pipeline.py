import pytest
from pathlib import Path
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.loaders import DocumentLoader


def test_unsupported_file_format(tmp_path):
    invalid_file = tmp_path / "test.xyz"
    invalid_file.write_text("dummy content")

    with pytest.raises(ValueError, match="Unsupported file format"):
        DocumentLoader.load_file(invalid_file)


def test_pipeline_text_file_processing(tmp_path):
    sample_file = tmp_path / "sample_report.txt"
    sample_file.write_text("Soil degradation affects agricultural productivity globally.")

    metadata = {
        "title": "Soil Quality Metrics",
        "source": "UNEP Report",
        "organization": "UNEP",
        "publication_year": 2024,
        "url": "https://unep.org/report",
        "topic": "Soil Health",
        "environmental_metrics": ["soil_degradation"],
        "geographic_scope": "Global",
        "document_type": "report"
    }

    pipeline = IngestionPipeline(chunk_size=500, chunk_overlap=50)
    result, chunks = pipeline.process_file(sample_file, metadata)

    assert result.status == "success"
    assert result.total_chunks == len(chunks)
    assert len(chunks) > 0
    assert chunks[0].metadata.organization == "UNEP"