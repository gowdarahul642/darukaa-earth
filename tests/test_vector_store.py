import pytest
from app.ingestion.schemas import DocumentChunk, DocumentMetadata
from app.embeddings.vector_store import VectorStoreManager


@pytest.fixture
def temp_vector_store(tmp_path):
    return VectorStoreManager(
        collection_name="test_collection",
        persist_dir=tmp_path / "chroma",
    )


def test_add_and_query_vector_store(temp_vector_store):
    meta = DocumentMetadata(
        title="Soil Organic Matter Impact",
        source="FAO Report",
        organization="FAO",
        publication_year=2024,
        url="https://fao.org/soil",
        topic="Soil Health",
        environmental_metrics=["soil_organic_carbon", "soil_moisture"],
        geographic_scope="Semi-Arid",
        document_type="report",
    )

    chunk1 = DocumentChunk(
        chunk_id="doc1_0",
        document_title=meta.title,
        chunk_index=0,
        content="Legume cover cropping significantly increases soil organic carbon and soil biological activity.",
        char_count=98,
        metadata=meta,
    )

    chunk2 = DocumentChunk(
        chunk_id="doc1_1",
        document_title=meta.title,
        chunk_index=1,
        content="Urban expansion drives land fragmentation and loss of native insect biodiversity.",
        char_count=87,
        metadata=meta,
    )

    # Index chunks
    added = temp_vector_store.add_chunks([chunk1, chunk2])
    assert added == 2
    assert temp_vector_store.count() == 2

    # Perform semantic query for soil carbon
    results = temp_vector_store.query_similar(query_text="How to increase soil organic carbon?", top_k=1)
    assert len(results) == 1
    assert "cover cropping" in results[0]["content"]
    assert results[0]["chunk_id"] == "doc1_0"