from typing import List, Dict, Any, Optional
from app.config import settings
from app.embeddings.vector_store import VectorStoreManager
from app.schemas.environmental_state import EnvironmentalState
from app.retrieval.schemas import RetrievedEvidence, RAGRetrievalResult


class EnvironmentalRetriever:
    """Retrieves scientific evidence based on composite multi-metric environmental queries."""

    def __init__(self, vector_store: Optional[VectorStoreManager] = None):
        self.vector_store = vector_store or VectorStoreManager()

    def build_composite_queries(self, state: EnvironmentalState) -> List[str]:
        """Synthesizes composite search queries directly from the EnvironmentalState model."""
        queries = []
        observed_conditions = []

        # Soil organic carbon lookup (organic_carbon_percent)
        soc = state.soil.organic_carbon_percent
        if soc is not None and soc < 1.0:
            observed_conditions.append("low soil organic carbon")
        if state.soil.ph is not None:
            observed_conditions.append(f"soil pH {state.soil.ph}")

        # Climate lookup (rainfall_category or rainfall_mm)
        rf_cat = state.climate.rainfall_category
        if rf_cat in ["low", "arid", "semi-arid"]:
            observed_conditions.append("low rainfall semi-arid climate")
        elif state.climate.rainfall_mm is not None and state.climate.rainfall_mm < 600:
            observed_conditions.append("low rainfall semi-arid climate")

        # Land management lookup (cropping_system or crop_type)
        cropping = state.land.cropping_system
        crop = state.land.crop_type or "crop"
        if cropping == "monoculture" or state.land.land_use_type == "cropland":
            observed_conditions.append(f"{crop} monoculture farming")

        # Synthesize multi-metric composite query
        if observed_conditions:
            composite_main = " + ".join(observed_conditions) + " + ecological restoration intervention"
            queries.append(composite_main)

        # Fallback multi-metric query
        queries.append("soil organic carbon biodiversity degradation intervention")
        return queries

    def retrieve_evidence(
        self,
        state: EnvironmentalState,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> RAGRetrievalResult:
        top_k = top_k or settings.retrieval_top_k
        min_score = min_score if min_score is not None else settings.retrieval_score_threshold

        composite_queries = self.build_composite_queries(state)
        raw_results = []
        seen_chunk_ids = set()

        for query in composite_queries:
            matches = self.vector_store.query_similar(query_text=query, top_k=top_k)
            for item in matches:
                chunk_id = item["chunk_id"]
                score = item["similarity_score"]

                if chunk_id not in seen_chunk_ids and score >= min_score:
                    seen_chunk_ids.add(chunk_id)

                    raw_metrics = item["metadata"].get("environmental_metrics", "")
                    metrics_list = (
                        raw_metrics.split(",") if isinstance(raw_metrics, str) and raw_metrics else []
                    )

                    evidence_item = RetrievedEvidence(
                        chunk_id=chunk_id,
                        content=item["content"],
                        document_title=item["metadata"].get(
                            "document_title", item["metadata"].get("title", "Unknown")
                        ),
                        organization=item["metadata"].get("organization", "Unknown"),
                        publication_year=int(item["metadata"].get("publication_year", 2024)),
                        url=item["metadata"].get("url", ""),
                        topic=item["metadata"].get("topic", "Ecology"),
                        environmental_metrics=metrics_list,
                        similarity_score=score,
                        query_used=query,
                    )
                    raw_results.append(evidence_item)

        raw_results.sort(key=lambda x: x.similarity_score, reverse=True)
        final_evidence = raw_results[:top_k]

        return RAGRetrievalResult(
            primary_query=composite_queries[0] if composite_queries else "",
            composite_queries=composite_queries,
            total_retrieved=len(final_evidence),
            evidence=final_evidence,
        )