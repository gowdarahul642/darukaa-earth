import pytest
from app.schemas.environmental_state import (
    EnvironmentalState,
    SoilState,
    ClimateState,
    LandState,
)
from app.retrieval.retriever import EnvironmentalRetriever
from app.reasoning.engine import MultiMetricReasoningEngine
from app.interventions.engine import InterventionEngine


def test_multi_metric_reasoning_and_interventions():
    # Construct test input scenario
    state = EnvironmentalState(
        soil=SoilState(organic_carbon_percent=0.3),
        climate=ClimateState(rainfall_category="low"),
        land=LandState(crop_type="wheat", cropping_system="monoculture"),
    )

    # Execute Phase 8 Reasoning Engine
    reasoning_engine = MultiMetricReasoningEngine()
    analysis = reasoning_engine.analyze(state)

    assert analysis.overall_vulnerability in ["High", "Critical"]
    assert len(analysis.anomalies) == 3
    assert len(analysis.interactions) >= 1

    # Execute Phase 5 Retrieval Pipeline
    retriever = EnvironmentalRetriever()
    retrieval_result = retriever.retrieve_evidence(state, top_k=2)

    # Execute Phase 9 Intervention Engine
    intervention_engine = InterventionEngine()
    actions = intervention_engine.evaluate_interventions(
        state=state, reasoning=analysis, retrieval_result=retrieval_result
    )

    assert len(actions) >= 1
    assert "cover crops" in actions[0].action.lower()
    assert len(actions[0].metrics_affected) > 0
    assert len(actions[0].trade_offs) > 0