import json
import re
from typing import Any, Dict, Optional, Tuple, Union
from geopy.geocoders import Nominatim

from app.extraction.schemas import ExtractionResult
from app.schemas.environmental_state import (
    ClimateState,
    EnvironmentalState,
    LandState,
    SoilState,
)


class EnvironmentalExtractor:
    """Extracts state, performs intent classification, and geocodes place names automatically."""

    def __init__(self):
        self.geolocator = Nominatim(user_agent="darukaa_earth_engine")

    def detect_intent(self, text: str) -> str:
        text_clean = text.strip().lower()

        # 1. Greetings
        greetings = [
            "hi",
            "hello",
            "hey",
            "greetings",
            "good morning",
            "good afternoon",
            "who are you",
            "help",
        ]
        if text_clean in greetings or (
            len(text_clean.split()) <= 2 and any(g in text_clean for g in greetings)
        ):
            return "greeting"

        # 2. Assessment Data Check (Requires digits or explicit farm/soil measurement markers)
        has_assessment_data = bool(
            re.search(r"\d", text_clean)
            or any(
                phrase in text_clean
                for phrase in [
                    "my farm",
                    "continuous wheat",
                    "located in",
                    "sandy loam",
                    "clay loam",
                    "silty clay",
                    "monoculture",
                    "cropping system",
                    "soil organic carbon",
                    "organic carbon",
                    "soc",
                    "ph level",
                    "rainfall category",
                ]
            )
        )

        if has_assessment_data:
            return "assessment"

        # 3. Everything else defaults to general query (e.g., "tell me about deforestation", "what is soil?")
        return "general_query"

    def _geocode_location(
        self, text: str
    ) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        location_patterns = [
            r"(?:in|near|at|around|farm in|located in)\s+([A-Z][a-zA-Z\s]+(?:,\s*[A-Z][a-zA-Z\s]+)*)",
            r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s*,\s*[A-Z][a-zA-Z]+)",
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                place_name = match.group(1).strip()
                try:
                    loc = self.geolocator.geocode(place_name, timeout=5)
                    if loc:
                        region = "semi-arid" if abs(loc.latitude) < 35 else "temperate"
                        return round(loc.latitude, 4), round(loc.longitude, 4), region
                except Exception:
                    pass
        return None, None, None

    def extract(self, input_data: Union[str, Dict[str, Any]]) -> ExtractionResult:
        if isinstance(input_data, dict):
            return self._extract_from_dict(input_data)

        try:
            parsed_json = json.loads(input_data)
            if isinstance(parsed_json, dict):
                return self._extract_from_dict(parsed_json)
        except (json.JSONDecodeError, TypeError):
            pass

        return self._extract_from_text(input_data)

    def _extract_from_dict(self, data: Dict[str, Any]) -> ExtractionResult:
        soil = SoilState(
            organic_carbon_percent=data.get("soil_organic_carbon")
            or data.get("organic_carbon"),
            ph=data.get("ph") or data.get("soil_ph"),
            moisture_category=data.get("soil_moisture"),
            texture=data.get("soil_texture"),
        )
        climate = ClimateState(
            rainfall_category=data.get("rainfall"),
            rainfall_mm=data.get("rainfall_mm"),
            temperature_c=data.get("temperature"),
        )
        land = LandState(
            crop_type=data.get("crop") or data.get("crop_type"),
            cropping_system=data.get("land_use") or data.get("cropping_system"),
            land_use_type=data.get(
                "land_use_type", "cropland" if data.get("crop") else None
            ),
        )
        state = EnvironmentalState(
            region=data.get("region"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            soil=soil,
            climate=climate,
            land=land,
        )
        return ExtractionResult(
            raw_input=json.dumps(data),
            extracted_state=state,
            confidence_score=1.0,
            extraction_method="structured_json",
        )

    def _extract_from_text(self, text: str) -> ExtractionResult:
        text_lower = text.lower()
        lat, lon, geo_region = self._geocode_location(text)

        region = geo_region
        for r in ["semi-arid", "arid", "tropical", "temperate", "mediterranean"]:
            if r in text_lower:
                region = r
                break

        # 1. Coordinates (Lat/Lon)
        coord_match = re.search(
            r"(?:lat|latitude)[^\d\-]*(-?\d+(?:\.\d+)?)[^\d\-]+(?:lon|lng|longitude)[^\d\-]*(-?\d+(?:\.\d+)?)",
            text_lower,
        )
        if coord_match:
            lat = float(coord_match.group(1))
            lon = float(coord_match.group(2))

        # 2. Soil Organic Carbon (SOC) - Handles "0.4% SOC" AND "SOC of 0.4%"
        soc = None
        soc_match = re.search(
            r"(\d+(?:\.\d+)?)\s*%?\s*(?:soil organic carbon|organic carbon|soc)|(?:soil organic carbon|organic carbon|soc)[^\d]*(\d+(?:\.\d+)?)\s*%?",
            text_lower,
        )
        if soc_match:
            soc = float(soc_match.group(1) or soc_match.group(2))

        # 3. pH Level - Handles "pH 6.5", "pH of 6.5", AND "6.5 pH"
        ph = None
        ph_match = re.search(
            r"(?:ph\s*(?:of|=|:)?\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*ph)",
            text_lower,
        )
        if ph_match:
            val = float(ph_match.group(1) or ph_match.group(2))
            if 3.0 <= val <= 10.0:
                ph = val

        # 4. Soil Texture
        texture = None
        for t in [
            "sandy loam",
            "clay loam",
            "silty clay",
            "loamy sand",
            "sandy",
            "clay",
            "loam",
            "silt",
        ]:
            if t in text_lower:
                texture = t
                break

        # 5. Degradation Indicators
        degradation = []
        for d in ["erosion", "compaction", "salinization", "crusting"]:
            if d in text_lower:
                degradation.append(d)

        # 6. Rainfall Category & Numerical Extraction
        rainfall_cat = None
        rainfall_mm = None

        mm_match = re.search(
            r"(?:(\d+(?:\.\d+)?)\s*mm\s*(?:of\s*)?rainfall|rainfall[^\d]*(\d+(?:\.\d+)?)\s*mm)",
            text_lower,
        )
        if mm_match:
            rainfall_mm = float(mm_match.group(1) or mm_match.group(2))
            if rainfall_mm < 500:
                rainfall_cat = "low"
            elif rainfall_mm <= 1000:
                rainfall_cat = "moderate"
            else:
                rainfall_cat = "high"
        else:
            if any(
                k in text_lower
                for k in ["low rainfall", "scarce rain", "arid", "dry region", "low rain"]
            ):
                rainfall_cat = "low"
            elif any(
                k in text_lower
                for k in ["moderate rainfall", "average rainfall", "medium rain"]
            ):
                rainfall_cat = "moderate"
            elif any(
                k in text_lower
                for k in ["high rainfall", "heavy rain", "abundant rainfall"]
            ):
                rainfall_cat = "high"

        # 7. Crop Type (Word boundaries prevent partial string false matches)
        crop = None
        crop_pattern = r"\b(wheat|maize|corn|rice|soybean|barley|sorghum|millet|cotton|sugarcane|pulses|chickpea|groundnut)\b"
        crop_match = re.search(crop_pattern, text_lower)
        if crop_match:
            crop = crop_match.group(1)

        # 8. Cropping System
        cropping_system = None
        if any(
            k in text_lower
            for k in ["monoculture", "continuous", "single crop", "mono-cropping"]
        ):
            cropping_system = "monoculture"
        elif any(
            k in text_lower
            for k in ["rotation", "intercropping", "cover crop"]
        ):
            cropping_system = "diversified"

        state = EnvironmentalState(
            region=region,
            latitude=lat,
            longitude=lon,
            soil=SoilState(
                organic_carbon_percent=soc,
                ph=ph,
                texture=texture,
                degradation_indicators=degradation if degradation else None,
            ),
            climate=ClimateState(
                rainfall_category=rainfall_cat,
                rainfall_mm=rainfall_mm,
            ),
            land=LandState(
                crop_type=crop,
                cropping_system=cropping_system,
                land_use_type="cropland" if crop else None,
            ),
        )

        return ExtractionResult(
            raw_input=text,
            extracted_state=state,
            confidence_score=0.85,
            extraction_method="rule_based_nlp_geocoded",
        )