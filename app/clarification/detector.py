from typing import List
from app.schemas.environmental_state import EnvironmentalState
from app.clarification.schemas import MissingInfoAnalysis


class MissingInformationDetector:
    """Detects missing key metrics required for valid multi-metric environmental reasoning."""

    CRITICAL_METRICS = {
        "soil.organic_carbon_percent": "Soil organic carbon percentage (or qualitative state)",
        "climate.rainfall_category": "Approximate annual rainfall or precipitation level",
        "land.crop_type": "Current crop type or land-use cover",
        "region": "Region or biome climate classification",
    }

    def analyze(self, state: EnvironmentalState) -> MissingInfoAnalysis:
        populated = state.populated_fields()
        missing_fields = []
        questions = []

        # Check critical metrics
        if "soil.organic_carbon_percent" not in populated and "soil.degradation_indicators" not in populated:
            missing_fields.append("soil.organic_carbon_percent")
            questions.append("1. Soil organic carbon percentage, if known (or overall soil health status).")

        if "climate.rainfall_category" not in populated and "climate.rainfall_mm" not in populated:
            missing_fields.append("climate.rainfall_category")
            questions.append("2. Approximate annual rainfall or rainfall category (e.g., low, moderate, arid).")

        if "land.crop_type" not in populated and "land.land_use_type" not in populated:
            missing_fields.append("land.crop_type")
            questions.append("3. Current land use or primary crop type.")

        if "region" not in populated:
            missing_fields.append("region")
            questions.append("4. Regional climate type (e.g., semi-arid, temperate, tropical).")

        is_sufficient = len(missing_fields) <= 1  # Allow evaluation if at most 1 metric is missing

        return MissingInfoAnalysis(
            is_sufficient=is_sufficient,
            missing_fields=missing_fields,
            clarification_questions=questions,
            missing_critical_count=len(missing_fields),
        )