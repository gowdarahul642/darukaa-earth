import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.schemas.environmental_state import EnvironmentalState
from app.reasoning.schemas import MultiMetricAnalysis
from app.retrieval.schemas import RAGRetrievalResult
from app.interventions.schemas import RecommendedAction, ScientificEvidenceCitation


class InterventionEngine:
    """Dynamically matches, filters, and ranks candidate interventions using registry data and RAG evidence."""

    def __init__(self, registry_path: Optional[Path] = None):
        if registry_path is None:
            registry_path = Path(__file__).resolve().parent.parent.parent / "data" / "interventions.json"
        
        self.interventions_db = self._load_registry(registry_path)

    def _load_registry(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
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

    def evaluate_interventions(
        self,
        state: EnvironmentalState,
        reasoning: MultiMetricAnalysis,
        retrieval_result: RAGRetrievalResult,
    ) -> List[RecommendedAction]:
        recommendations: List[RecommendedAction] = []

        citations = [
            ScientificEvidenceCitation(
                title=item.document_title,
                organization=item.organization,
                publication_year=item.publication_year,
                url=item.url,
            )
            for item in retrieval_result.evidence
        ]

        for item in self.interventions_db:
            conditions = item.get("suitable_conditions", {})
            is_suitable = True

            # Evaluate suitability rules dynamically
            for path, rule in conditions.items():
                val = self._get_metric_value(state, path)
                if val is None:
                    continue

                op = rule.get("operator")
                if op == "<" and isinstance(val, (int, float)) and not (val < rule["threshold"]):
                    is_suitable = False
                elif op == "in" and val not in rule.get("values", []):
                    is_suitable = False

            if is_suitable:
                confidence = "High" if citations else "Medium"
                recommendations.append(
                    RecommendedAction(
                        action=item["action"],
                        why_it_works=item["why_it_works"],
                        environmental_mechanism=item["environmental_mechanism"],
                        metrics_affected=item["target_metrics"],
                        time_horizon=item["time_horizon"],
                        evidence=citations[:2] if citations else [],
                        confidence=confidence,
                        confidence_rationale="Matched dynamically based on environmental suitability rules and retrieved literature.",
                        trade_offs=item["trade_offs"],
                        monitoring=item["monitoring"],
                    )
                )

        return recommendations