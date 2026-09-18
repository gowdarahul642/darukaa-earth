import json
from typing import List, Optional
from app.clarification.schemas import MissingInfoAnalysis
from app.interventions.schemas import RecommendedAction
from app.reasoning.schemas import MultiMetricAnalysis
from app.retrieval.schemas import RAGRetrievalResult
from app.schemas.environmental_state import EnvironmentalState

SYSTEM_PROMPT = """You are DARUKAA.EARTH, an expert AI Environmental Scientist.
Your task is to synthesize structured environmental data, multi-metric reasoning analysis, and retrieved scientific evidence into a clear, natural, and scientifically rigorous report.

STRICT GUIDELINES:
1. Generate natural, dynamic prose. Do not copy exact robotic templates.
2. Rely EXCLUSIVELY on the provided evidence and reasoning context. Never fabricate citations or numbers.
3. Keep the output formatted cleanly in Markdown under these headers:
   ## Environmental Assessment
   ## Key Interactions
   ## Recommended Actions
   ## Missing Information (include only if critical variables are missing)
"""


def build_synthesis_prompt(
    state: EnvironmentalState,
    analysis: MultiMetricAnalysis,
    retrieval: RAGRetrievalResult,
    actions: List[RecommendedAction],
    clarification: Optional[MissingInfoAnalysis] = None,
) -> str:
    evidence_items = [
        {
            "title": item.document_title,
            "organization": item.organization,
            "year": item.publication_year,
            "url": item.url,
            "excerpt": item.content[:200],
        }
        for item in retrieval.evidence
    ]

    candidate_actions = [
        {
            "action": act.action,
            "why_it_works": act.why_it_works,
            "environmental_mechanism": act.environmental_mechanism,
            "metrics_affected": act.metrics_affected,
            "time_horizon": act.time_horizon,
            "trade_offs": act.trade_offs,
            "monitoring": act.monitoring,
        }
        for act in actions
    ]

    context = {
        "environmental_state": state.populated_fields(),
        "vulnerability_level": analysis.overall_vulnerability,
        "anomalies": [a.model_dump() for a in analysis.anomalies],
        "interactions": [i.model_dump() for i in analysis.interactions],
        "candidate_interventions": candidate_actions,
        "retrieved_scientific_evidence": evidence_items,
        "missing_fields": clarification.missing_fields if clarification else [],
    }

    return f"Synthesize a complete ecological report based on this grounded environmental context:\n\n{json.dumps(context, indent=2)}\n\nWrite a professional scientific assessment in Markdown."