import pytest
from app.extraction.extractor import EnvironmentalExtractor
from app.clarification.detector import MissingInformationDetector


def test_json_and_text_extraction():
    extractor = EnvironmentalExtractor()

    # Test JSON input
    json_input = {
        "region": "semi-arid",
        "soil_organic_carbon": 0.3,
        "rainfall": "low",
        "crop": "wheat",
        "land_use": "monoculture",
    }
    res_json = extractor.extract(json_input)
    assert res_json.extracted_state.soil.organic_carbon_percent == 0.3
    assert res_json.extracted_state.land.crop_type == "wheat"

    # Test Natural Language input
    nl_input = "My farm is in a semi-arid region. I grow wheat continuously. Rainfall has been low and soil organic carbon is around 0.3%."
    res_nl = extractor.extract(nl_input)
    assert res_nl.extracted_state.region == "semi-arid"
    assert res_nl.extracted_state.soil.organic_carbon_percent == 0.3
    assert res_nl.extracted_state.climate.rainfall_category == "low"


def test_missing_information_detector():
    extractor = EnvironmentalExtractor()
    detector = MissingInformationDetector()

    # Complete state
    full_input = {
        "region": "semi-arid",
        "soil_organic_carbon": 0.3,
        "rainfall": "low",
        "crop": "wheat",
    }
    full_state = extractor.extract(full_input).extracted_state
    analysis_full = detector.analyze(full_state)
    assert analysis_full.is_sufficient is True
    assert len(analysis_full.missing_fields) == 0

    # Incomplete state
    sparse_input = "Biodiversity is declining on my land."
    sparse_state = extractor.extract(sparse_input).extracted_state
    analysis_sparse = detector.analyze(sparse_state)
    assert analysis_sparse.is_sufficient is False
    assert len(analysis_sparse.clarification_questions) > 0