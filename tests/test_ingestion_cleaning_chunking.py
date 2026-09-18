import pytest
from app.ingestion.cleaning import TextCleaner
from app.ingestion.chunking import DocumentChunker
from app.ingestion.schemas import DocumentMetadata


def test_clean_text():
    raw_text = "Soil organic  carbon is key.\nPage 1 of 10\nRe- \nsoration is vital."
    cleaned = TextCleaner.clean_text(raw_text)
    assert "Soil organic carbon is key." in cleaned
    assert "Page 1 of 10" not in cleaned


def test_chunker_basic():
    meta = DocumentMetadata(
        title="Soil Organic Carbon Study",
        source="FAO",
        organization="FAO",
        publication_year=2023,
        url="https://fao.org/sample",
        topic="Soil Degradation",
        environmental_metrics=["soil_organic_carbon"],
        geographic_scope="Global",
        document_type="report"
    )

    sample_text = "Soil organic carbon (SOC) is an important indicator of soil health. " * 30
    chunker = DocumentChunker(chunk_size=300, chunk_overlap=50)
    chunks = chunker.chunk_text(sample_text, meta)

    assert len(chunks) > 1
    assert chunks[0].document_title == "Soil Organic Carbon Study"
    assert len(chunks[0].content) <= 300


def test_chunker_invalid_overlap():
    with pytest.raises(ValueError):
        DocumentChunker(chunk_size=100, chunk_overlap=150)