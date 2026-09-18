import pytest
from app.schemas.environmental_state import (
    EnvironmentalState,
    SoilState,
    ClimateState,
    LandState,
)
from app.retrieval.retriever import EnvironmentalRetriever


def test_composite_query_building():
    state = EnvironmentalState(
        soil=SoilState(organic_carbon_percent=0.3),
        climate=ClimateState(rainfall_category="low"),
        land=LandState(crop_type="wheat", cropping_system="monoculture"),
    )

    retriever = EnvironmentalRetriever()
    queries = retriever.build_composite_queries(state)

    assert len(queries) >= 1
    assert "low soil organic carbon" in queries[0]
    assert "low rainfall" in queries[0]
    assert "wheat monoculture" in queries[0]


def test_retrieval_execution():
    state = EnvironmentalState(
        soil=SoilState(organic_carbon_percent=0.3),
        climate=ClimateState(rainfall_category="low"),
        land=LandState(crop_type="wheat", cropping_system="monoculture"),
    )

    retriever = EnvironmentalRetriever()
    result = retriever.retrieve_evidence(state, top_k=3)

    assert result.total_retrieved > 0
    assert len(result.evidence) <= 3
    assert result.evidence[0].similarity_score > 0.0