"""
EnvironmentalState schema.

This is the single shared representation of "everything currently known
about one piece of land" that flows through the entire system:

    NL text / JSON input  --(Phase 6 extraction)-->  EnvironmentalState
    EnvironmentalState     --(Phase 7)-->             missing-field detection
    EnvironmentalState     --(Phase 8)-->             multi-metric reasoning
    EnvironmentalState     --(Phase 5)-->             retrieval query construction
    EnvironmentalState     --(Phase 11)-->            conversation memory (persisted)

Design principles (do not violate these in later phases):

1. Every field is Optional. Partial information is the normal case, not an
   error — the clarification engine (Phase 7) decides what's missing, this
   schema just represents "what we know so far" honestly.
2. No field is ever guessed or defaulted to a plausible-looking value here.
   Unset means unset (None), never 0, never "unknown" as a string.
3. Extensibility without rewrites: every category has an `extra_metrics`
   dict for variables not yet promoted to a named field. When a new metric
   proves important, promote it to a named field later — existing data
   already flowing through `extra_metrics` is not lost or broken by that
   change.
4. Multiple representations of the same real-world quantity are allowed on
   purpose (e.g. `rainfall_mm` AND `rainfall_category`) because environmental
   data legitimately arrives both as precise measurements and as qualitative
   descriptions ("rainfall has been low"). Downstream reasoning should prefer
   the quantitative field when present and fall back to the qualitative one.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator



class SoilState(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    ph: Optional[float] = Field(default=None, ge=0.0, le=14.0)
    soil_organic_carbon: Optional[float] = Field(
        default=None, 
        ge=0.0, 
        le=100.0, 
        alias="organic_carbon",
        description="Soil organic carbon percentage"
    )
    soil_moisture: Optional[str] = Field(default=None)
    soil_texture: Optional[str] = Field(default=None)
    degradation_level: Optional[str] = Field(default=None)

class _MetricGroup(BaseModel):
    """Base class for all environmental metric categories.

    Provides the shared `extra_metrics` extensibility field and a helper to
    check whether the group carries any information at all.
    """

    model_config = ConfigDict(extra="forbid")

    extra_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Escape hatch for metrics not yet promoted to a named field. "
        "Never silently dropped; safe place for new variables.",
    )

    def is_empty(self) -> bool:
        for name, _ in self.model_fields.items():
            if name == "extra_metrics":
                continue
            if getattr(self, name) is not None:
                return False
        return len(self.extra_metrics) == 0

    def populated(self) -> dict[str, Any]:
        """Return only the fields that are actually set (non-None), flat."""
        out = {
            name: getattr(self, name)
            for name in self.model_fields
            if name != "extra_metrics" and getattr(self, name) is not None
        }
        out.update(self.extra_metrics)
        return out


class SoilState(_MetricGroup):
    """SOIL metrics."""

    ph: Optional[float] = Field(default=None, description="Soil pH, e.g. 6.5")
    organic_carbon_percent: Optional[float] = Field(
        default=None, description="Soil organic carbon (SOC), percent by weight, e.g. 0.3"
    )
    moisture_percent: Optional[float] = Field(default=None, description="Volumetric soil moisture, percent")
    moisture_category: Optional[str] = Field(
        default=None, description="Qualitative moisture level, e.g. 'low', 'moderate', 'high'"
    )
    texture: Optional[str] = Field(default=None, description="e.g. 'sandy loam', 'clay', 'silt'")
    degradation_indicators: Optional[list[str]] = Field(
        default=None, description="e.g. ['erosion', 'compaction', 'salinization']"
    )


class ClimateState(_MetricGroup):
    """CLIMATE metrics."""

    temperature_c: Optional[float] = Field(default=None, description="Mean/representative temperature, Celsius")
    rainfall_mm: Optional[float] = Field(default=None, description="Annual rainfall, millimeters")
    rainfall_category: Optional[str] = Field(
        default=None, description="Qualitative rainfall level, e.g. 'low', 'moderate', 'high'"
    )
    rainfall_variability: Optional[str] = Field(
        default=None, description="e.g. 'highly variable', 'stable', 'increasingly erratic'"
    )
    drought_conditions: Optional[str] = Field(default=None, description="e.g. 'none', 'mild', 'severe', 'recurrent'")


class LandState(_MetricGroup):
    """LAND metrics.

    Note: `habitat_diversity` is modeled here (structural land-cover
    perspective) rather than duplicated on BiodiversityState. Reasoning
    logic that needs habitat diversity for biodiversity inference should
    read it from here — see app.reasoning docstring (Phase 8) for how the
    two categories are cross-referenced.
    """

    land_use_type: Optional[str] = Field(default=None, description="e.g. 'cropland', 'forest', 'urban', 'grassland'")
    land_cover_type: Optional[str] = Field(default=None, description="e.g. 'annual crop', 'closed forest'")
    crop_type: Optional[str] = Field(default=None, description="e.g. 'wheat', 'maize', 'coffee'")
    cropping_system: Optional[str] = Field(
        default=None, description="'monoculture', 'polyculture', 'intercropped', 'agroforestry', etc."
    )
    vegetation_cover_percent: Optional[float] = Field(default=None, description="Percent ground vegetation cover")
    habitat_diversity: Optional[str] = Field(
        default=None, description="Qualitative structural habitat diversity, e.g. 'low', 'moderate', 'high'"
    )
    fragmentation: Optional[str] = Field(
        default=None, description="e.g. 'none', 'moderate', 'severe', or a patch-size description"
    )


class BiodiversityState(_MetricGroup):
    """BIODIVERSITY metrics."""

    species_richness: Optional[float] = Field(
        default=None, description="Observed/estimated number of species, if known"
    )
    species_diversity: Optional[str] = Field(
        default=None, description="Qualitative or index-based description, e.g. 'low', 'Shannon index 1.2'"
    )
    pollinator_presence: Optional[str] = Field(default=None, description="e.g. 'absent', 'occasional', 'abundant'")
    native_vegetation_percent: Optional[float] = Field(default=None, description="Percent native vegetation cover")
    invasive_species_present: Optional[bool] = Field(default=None)
    invasive_species: Optional[list[str]] = Field(default=None, description="Named invasive species, if known")


class HumanImpactState(_MetricGroup):
    """HUMAN IMPACT metrics."""

    deforestation: Optional[str] = Field(default=None, description="e.g. 'none', 'recent', 'historical', 'ongoing'")
    pollution: Optional[str] = Field(default=None, description="e.g. 'none', 'agrochemical runoff', 'industrial'")
    urbanization: Optional[str] = Field(default=None, description="e.g. 'none', 'nearby', 'encroaching'")
    agricultural_intensity: Optional[str] = Field(default=None, description="e.g. 'low', 'moderate', 'high'")
    habitat_disturbance: Optional[str] = Field(default=None, description="e.g. 'grazing pressure', 'trampling'")
    water_extraction: Optional[str] = Field(default=None, description="e.g. 'none', 'moderate', 'heavy irrigation'")


class GeoEnrichmentStatus(BaseModel):
    """Explicit record of whether/what geographic enrichment was applied.

    Populated in later phases (Phase 13 groundwork). The system must never
    silently fabricate spatially-derived values — this record makes it
    auditable which fields (if any) came from a spatial dataset versus the
    user directly.
    """

    model_config = ConfigDict(extra="forbid")

    attempted: bool = Field(default=False)
    available: bool = Field(default=False, description="Whether a real spatial dataset/service was actually used.")
    enriched_fields: list[str] = Field(default_factory=list)
    note: Optional[str] = Field(
        default=None,
        description="Human-readable explanation, e.g. 'Geographic enrichment unavailable in this deployment.'",
    )


class EnvironmentalState(BaseModel):
    """The complete, partially-known environmental picture for one site.

    This is what gets extracted from user input (Phase 6), checked for gaps
    (Phase 7), reasoned over (Phase 8), and persisted as conversation memory
    (Phase 11). It is intentionally a plain data container: it has no
    knowledge of scientific evidence, interventions, or LLM output.
    """

    model_config = ConfigDict(extra="forbid")

    region: Optional[str] = Field(default=None, description="e.g. 'semi-arid', 'tropical lowland', free text or biome")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)

    soil: SoilState = Field(default_factory=SoilState)
    climate: ClimateState = Field(default_factory=ClimateState)
    land: LandState = Field(default_factory=LandState)
    biodiversity: BiodiversityState = Field(default_factory=BiodiversityState)
    human_impact: HumanImpactState = Field(default_factory=HumanImpactState)

    geo_enrichment: GeoEnrichmentStatus = Field(default_factory=GeoEnrichmentStatus)

    extra_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Top-level escape hatch for entirely new categories not yet modeled.",
    )

    @model_validator(mode="after")
    def _require_lat_lon_together(self) -> "EnvironmentalState":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self

    # ------------------------------------------------------------------
    # Introspection helpers (used by later phases; kept minimal on purpose)
    # ------------------------------------------------------------------

    def is_empty(self) -> bool:
        """True if literally nothing has been provided yet."""
        if self.region is not None or self.latitude is not None:
            return False
        groups = (self.soil, self.climate, self.land, self.biodiversity, self.human_impact)
        return all(g.is_empty() for g in groups) and len(self.extra_metrics) == 0

    def populated_fields(self) -> dict[str, Any]:
        """Flat {"category.field": value} dict of everything currently known.

        Used by the clarification engine (Phase 7) to know what's already
        answered, and by prompt construction (Phase 10) to summarize known
        facts without re-deriving them from the nested structure each time.
        """
        flat: dict[str, Any] = {}
        if self.region is not None:
            flat["region"] = self.region
        if self.latitude is not None:
            flat["latitude"] = self.latitude
            flat["longitude"] = self.longitude
        for group_name in ("soil", "climate", "land", "biodiversity", "human_impact"):
            group: _MetricGroup = getattr(self, group_name)
            for field_name, value in group.populated().items():
                flat[f"{group_name}.{field_name}"] = value
        flat.update({f"extra.{k}": v for k, v in self.extra_metrics.items()})
        return flat

    def merge(self, other: "EnvironmentalState") -> "EnvironmentalState":
        """Combine this state with newer information from `other`.

        Rule: `other`'s non-None values win (they represent newer/more
        specific information from a later message); anything `other` leaves
        unset is preserved from `self`. Lists are unioned (dedup, order
        preserved); dicts are merged with `other` winning on key conflicts.

        This is the core operation behind multi-turn conversational memory
        (Phase 11): each new user message produces a small EnvironmentalState
        that gets merged into the conversation's running profile rather than
        replacing it.
        """
        return _merge_models(self, other)  # type: ignore[return-value]


def _merge_models(a: BaseModel, b: BaseModel) -> BaseModel:
    """Generic recursive merge for any two instances of the same BaseModel type.

    Works uniformly across EnvironmentalState and all _MetricGroup subclasses
    without hardcoding field names, so adding a new field or a new metric
    group later requires zero changes here.
    """
    assert type(a) is type(b), "merge() requires two instances of the same model type"
    merged_values: dict[str, Any] = {}
    for name in a.model_fields:
        a_val = getattr(a, name)
        b_val = getattr(b, name)
        if isinstance(a_val, BaseModel) and isinstance(b_val, BaseModel):
            merged_values[name] = _merge_models(a_val, b_val)
        elif isinstance(a_val, dict) and isinstance(b_val, dict):
            merged_values[name] = {**a_val, **b_val}
        elif isinstance(a_val, list) and isinstance(b_val, list):
            merged_values[name] = list(dict.fromkeys([*a_val, *b_val]))
        elif b_val is not None:
            merged_values[name] = b_val
        else:
            merged_values[name] = a_val
    return type(a)(**merged_values)
