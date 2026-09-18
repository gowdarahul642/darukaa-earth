from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MetricAnomaly(BaseModel):
    metric_name: str
    observed_value: Any
    severity: str  # "mild", "moderate", "severe"
    ecological_impact: str


class EcologicalInteraction(BaseModel):
    primary_metric: str
    interacting_metrics: List[str]
    ecological_mechanism: str
    cascading_effects: List[str]


class MultiMetricAnalysis(BaseModel):
    anomalies: List[MetricAnomaly]
    interactions: List[EcologicalInteraction]
    primary_pressures: List[str]
    overall_vulnerability: str  # "Low", "Medium", "High", "Critical"