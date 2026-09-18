import pytest
from app.schemas.environmental_state import EnvironmentalState, SoilState, ClimateState, LandState
from app.reasoning.engine import MultiMetricReasoningEngine
from app.retrieval.retriever import EnvironmentalRetriever
from app.interventions.engine import InterventionEngine
from app.llm.synthesizer import ScientificSynthesizer


def test_full_pipeline_synthesis():
    state = EnvironmentalState(
        region="semi-arid",
        soil=SoilState(organic_carbon_percent=0.3),
        climate=ClimateState(rainfall_category="low"),
        land=LandState(crop_type="wheat", cropping_system="monoculture"),
    )

    reasoning = MultiMetricReasoningEngine().analyze(state)
    retrieval = EnvironmentalRetriever().retrieve_evidence(state, top_k=2)
    actions = InterventionEngine().evaluate_interventions(state, reasoning, retrieval)

    synthesizer = ScientificSynthesizer()
    report = synthesizer.synthesize_report(
        state=state, analysis=reasoning, retrieval=retrieval, actions=actions
    )

    assert "## Environmental Assessment" in report
    assert "## Key Interactions" in report
    assert "## Recommended Actions" in report
    assert "Recommendation 1" in report
    assert "soil.organic_carbon_percent" in report