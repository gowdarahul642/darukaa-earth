from typing import List, Optional
from app.clarification.schemas import MissingInfoAnalysis
from app.interventions.schemas import RecommendedAction
from app.llm.prompts import SYSTEM_PROMPT, build_synthesis_prompt
from app.llm.providers import BaseLLMProvider, MockLLMProvider, get_llm_provider
from app.reasoning.schemas import MultiMetricAnalysis
from app.retrieval.schemas import RAGRetrievalResult
from app.schemas.environmental_state import EnvironmentalState


class ScientificSynthesizer:
    """Routes grounded environmental context directly to the LLM for dynamic prose synthesis."""

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider or get_llm_provider()

    def synthesize_report(
        self,
        state: EnvironmentalState,
        analysis: MultiMetricAnalysis,
        retrieval: RAGRetrievalResult,
        actions: List[RecommendedAction],
        clarification: Optional[MissingInfoAnalysis] = None,
    ) -> str:
        if isinstance(self.provider, MockLLMProvider):
            return self._build_deterministic_report(
                state, analysis, retrieval, actions, clarification
            )

        prompt = build_synthesis_prompt(
            state=state,
            analysis=analysis,
            retrieval=retrieval,
            actions=actions,
            clarification=clarification,
        )
        return self.provider.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)

    def _build_deterministic_report(
        self,
        state: EnvironmentalState,
        analysis: MultiMetricAnalysis,
        retrieval: RAGRetrievalResult,
        actions: List[RecommendedAction],
        clarification: Optional[MissingInfoAnalysis] = None,
    ) -> str:
        report = []

        report.append("## Environmental Assessment")
        report.append(
            f"Site region classified as **{state.region or 'unspecified'}** with an overall ecological vulnerability rating of **{analysis.overall_vulnerability}**."
        )
        if analysis.anomalies:
            report.append("\n**Observed Anomalies:**")
            for a in analysis.anomalies:
                report.append(
                    f"- **{a.metric_name}** ({a.observed_value}): {a.ecological_impact}"
                )
        report.append("\n")

        report.append("## Key Interactions")
        if analysis.interactions:
            for inter in analysis.interactions:
                report.append(
                    f"### {inter.primary_metric} ↔ {', '.join(inter.interacting_metrics)}"
                )
                report.append(f"**Mechanism:** {inter.ecological_mechanism}")
                report.append("**Cascading Effects:**")
                for c in inter.cascading_effects:
                    report.append(f"  - {c}")
        else:
            report.append(
                "No critical multi-metric compound interactions detected for current values.\n"
            )
        report.append("\n")

        report.append("## Recommended Actions\n")
        for idx, act in enumerate(actions, 1):
            report.append(f"### Recommendation {idx}")
            report.append(f"**Action:** {act.action}")
            report.append(f"**Why it works:** {act.why_it_works}")
            report.append(
                f"**Environmental mechanism:** {act.environmental_mechanism}"
            )
            report.append(f"**Metrics affected:** {', '.join(act.metrics_affected)}")
            report.append(f"**Time horizon:** {act.time_horizon}")
            report.append("**Evidence:**")
            if act.evidence:
                for ev in act.evidence:
                    report.append(
                        f"  - *{ev.title}* ({ev.organization}, {ev.publication_year}) - [{ev.url}]({ev.url})"
                    )
            else:
                report.append(
                    "  - *Available evidence is insufficient to provide a reliable quantitative estimate for this specific condition.*"
                )
            report.append(
                f"**Confidence:** {act.confidence} — {act.confidence_rationale}"
            )
            report.append(f"**Trade-offs:** {'; '.join(act.trade_offs)}")
            report.append(f"**Monitoring:** {'; '.join(act.monitoring)}\n")

        if (
            clarification
            and clarification.clarification_questions
            and not clarification.is_sufficient
        ):
            report.append("## Missing Information")
            report.append("To refine this analysis further, please provide:")
            for q in clarification.clarification_questions:
                report.append(f"{q}")

        return "\n".join(report)