from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.api.schemas import ChatResponse
from app.clarification.detector import MissingInformationDetector
from app.extraction.extractor import EnvironmentalExtractor
from app.interventions.engine import InterventionEngine
from app.llm.synthesizer import ScientificSynthesizer
from app.memory.manager import ConversationMemoryManager
from app.reasoning.engine import MultiMetricReasoningEngine
from app.retrieval.retriever import EnvironmentalRetriever
from app.schemas.environmental_state import EnvironmentalState


class PipelineOrchestrator:
    """Orchestrates intent detection, geocoding, reasoning, RAG, and visualization payloads."""

    def __init__(self, db: Session):
        self.db = db
        self.memory = ConversationMemoryManager(db)
        self.extractor = EnvironmentalExtractor()
        self.detector = MissingInformationDetector()
        self.reasoning = MultiMetricReasoningEngine()
        self.retriever = EnvironmentalRetriever()
        self.interventions = InterventionEngine()
        self.synthesizer = ScientificSynthesizer()

    def _compute_vulnerability_scores(
        self, state: EnvironmentalState
    ) -> Dict[str, float]:
        soil_risk, climate_risk, land_risk, biodiversity_risk = (
            20.0,
            20.0,
            20.0,
            20.0,
        )

        if (
            state.soil.organic_carbon_percent is not None
            and state.soil.organic_carbon_percent < 1.0
        ):
            soil_risk += 60.0
        if state.climate.rainfall_category in ["low", "arid", "semi-arid"]:
            climate_risk += 50.0
        if state.land.cropping_system in ["monoculture", "continuous"]:
            land_risk += 55.0
            biodiversity_risk += 45.0

        return {
            "Soil Health Risk": min(soil_risk, 100.0),
            "Climate Stress": min(climate_risk, 100.0),
            "Land Monoculture Pressure": min(land_risk, 100.0),
            "Biodiversity Loss Risk": min(biodiversity_risk, 100.0),
        }

    def process_message(
        self, message: str, conversation_id: Optional[str] = None
    ) -> ChatResponse:
        session_id = self.memory.get_or_create_session(conversation_id)
        intent = self.extractor.detect_intent(message)

        # 1. Handle Greetings
        if intent == "greeting":
            current_state = self.memory.get_profile(session_id)
            greeting_msg = (
                "Hello! I am **DARUKAA.EARTH**, your Scientific Environmental Intelligence Assistant.\n\n"
                "Ask me any general environmental science question, or describe your farm location and soil metrics "
                "to run an ecological assessment."
            )
            return ChatResponse(
                conversation_id=session_id,
                intent_type="greeting",
                response=greeting_msg,
                environmental_state=current_state,
                is_sufficient=False,
                missing_fields=[],
                vulnerability_scores={
                    "Soil Health Risk": 0,
                    "Climate Stress": 0,
                    "Land Monoculture Pressure": 0,
                    "Biodiversity Loss Risk": 0,
                },
                evidence_count=0,
            )

        # 2. Handle General Informational Queries ("what is water?", "how does photosynthesis work?")
        if intent == "general_query":
            current_state = self.memory.get_profile(session_id)
            system_prompt = (
                "You are DARUKAA.EARTH, an expert AI Environmental Scientist. "
                "Answer general scientific, ecological, and conversational questions concisely, accurately, and naturally."
            )
            answer = self.synthesizer.provider.generate(
                prompt=message, system_prompt=system_prompt
            )

            return ChatResponse(
                conversation_id=session_id,
                intent_type="general_query",
                response=answer,
                environmental_state=current_state,
                is_sufficient=True,
                missing_fields=[],
                vulnerability_scores={
                    "Soil Health Risk": 0,
                    "Climate Stress": 0,
                    "Land Monoculture Pressure": 0,
                    "Biodiversity Loss Risk": 0,
                },
                evidence_count=0,
            )

        # 3. Handle Full Environmental Land Assessment
        extraction_res = self.extractor.extract(message)
        updated_state = self.memory.update_profile(
            session_id, extraction_res.extracted_state
        )

        clarification = self.detector.analyze(updated_state)
        analysis = self.reasoning.analyze(updated_state)
        retrieval = self.retriever.retrieve_evidence(updated_state)
        actions = self.interventions.evaluate_interventions(
            updated_state, analysis, retrieval
        )
        vulnerability_scores = self._compute_vulnerability_scores(updated_state)

        report = self.synthesizer.synthesize_report(
            state=updated_state,
            analysis=analysis,
            retrieval=retrieval,
            actions=actions,
            clarification=clarification,
        )

        return ChatResponse(
            conversation_id=session_id,
            intent_type="assessment",
            response=report,
            environmental_state=updated_state,
            is_sufficient=clarification.is_sufficient,
            missing_fields=clarification.missing_fields,
            vulnerability_scores=vulnerability_scores,
            evidence_count=retrieval.total_retrieved,
        )
