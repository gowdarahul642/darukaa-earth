import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.schemas.environmental_state import EnvironmentalState
from app.reasoning.schemas import (
    MetricAnomaly,
    EcologicalInteraction,
    MultiMetricAnalysis,
)


class MultiMetricReasoningEngine:
    """Evaluates non-linear environmental variable interactions dynamically using a rule graph."""

    def __init__(self, graph_path: Optional[Path] = None):
        if graph_path is None:
            graph_path = Path(__file__).resolve().parent.parent.parent / "data" / "ecological_graph.json"
        
        self.graph_data = self._load_graph(graph_path)

    def _load_graph(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"anomalies": [], "interactions": []}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_metric_value(self, state: EnvironmentalState, path_str: str) -> Any:
        parts = path_str.split(".")
        curr = state
        for p in parts:
            if hasattr(curr, p):
                curr = getattr(curr, p)
            else:
                return None
        return curr

    def analyze(self, state: EnvironmentalState) -> MultiMetricAnalysis:
        anomalies: List[MetricAnomaly] = []
        triggered_paths = set()
        primary_pressures: List[str] = []

        # 1. Dynamic Anomaly Evaluation
        for rule in self.graph_data.get("anomalies", []):
            path = rule["metric_path"]
            val = self._get_metric_value(state, path)

            if val is None:
                continue

            is_anomaly = False
            op = rule.get("operator")

            if op == "<" and isinstance(val, (int, float)) and val < rule["threshold"]:
                is_anomaly = True
            elif op == "in" and val in rule.get("values", []):
                is_anomaly = True

            if is_anomaly:
                triggered_paths.add(path)
                severity = rule.get("severity", "moderate")

                # Check nested severity overrides
                for s_rule in rule.get("severity_rules", []):
                    if s_rule["operator"] == "<" and isinstance(val, (int, float)) and val < s_rule["threshold"]:
                        severity = s_rule["severity"]

                anomalies.append(
                    MetricAnomaly(
                        metric_name=path,
                        observed_value=val,
                        severity=severity,
                        ecological_impact=rule["impact"],
                    )
                )
                if rule.get("pressure_label") not in primary_pressures:
                    primary_pressures.append(rule["pressure_label"])

        # 2. Dynamic Interaction Graph Traversal
        interactions: List[EcologicalInteraction] = []
        for inter in self.graph_data.get("interactions", []):
            reqs = inter.get("required_anomalies", [])
            if all(r in triggered_paths for r in reqs):
                interactions.append(
                    EcologicalInteraction(
                        primary_metric=inter["primary_metric"],
                        interacting_metrics=inter["interacting_metrics"],
                        ecological_mechanism=inter["ecological_mechanism"],
                        cascading_effects=inter["cascading_effects"],
                    )
                )

        # 3. Dynamic Overall Vulnerability Scoring
        vulnerability = "Low"
        if len(primary_pressures) >= 3:
            vulnerability = "Critical"
        elif len(primary_pressures) == 2:
            vulnerability = "High"
        elif len(primary_pressures) == 1:
            vulnerability = "Medium"

        return MultiMetricAnalysis(
            anomalies=anomalies,
            interactions=interactions,
            primary_pressures=primary_pressures,
            overall_vulnerability=vulnerability,
        )