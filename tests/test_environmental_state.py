"""
Phase 2 tests: EnvironmentalState schema.

Covers the properties the rest of the system will depend on:
- partial construction is normal, not an error
- lat/lon must come as a pair
- merge() prefers newer non-None values but never discards older ones
- merge() unions lists and dicts rather than overwriting them
- extra_metrics absorbs unmodeled variables without validation errors
- populated_fields()/is_empty() reflect what's actually set
"""

import pytest
from pydantic import ValidationError

from app.schemas import EnvironmentalState, SoilState


def test_empty_state_is_valid_and_empty():
    state = EnvironmentalState()
    assert state.is_empty()
    assert state.populated_fields() == {}


def test_partial_construction_is_normal():
    state = EnvironmentalState(region="semi-arid", soil=SoilState(organic_carbon_percent=0.3))
    assert not state.is_empty()
    assert state.soil.organic_carbon_percent == 0.3
    assert state.soil.ph is None  # unset, not defaulted to anything


def test_lat_lon_must_be_paired():
    with pytest.raises(ValidationError):
        EnvironmentalState(latitude=18.52)  # longitude missing


def test_lat_lon_out_of_range_rejected():
    with pytest.raises(ValidationError):
        EnvironmentalState(latitude=999.0, longitude=73.85)


def test_extra_metrics_absorb_unmodeled_variables():
    """A variable not yet promoted to a named field must not break validation."""
    state = EnvironmentalState(
        soil=SoilState(extra_metrics={"cation_exchange_capacity": 12.4}),
        extra_metrics={"soundscape_index": "low"},
    )
    assert state.soil.extra_metrics["cation_exchange_capacity"] == 12.4
    assert state.populated_fields()["soil.cation_exchange_capacity"] == 12.4
    assert state.populated_fields()["extra.soundscape_index"] == "low"


def test_forbids_truly_unknown_top_level_fields():
    """extra='forbid' + extra_metrics means unmodeled fields must go through
    extra_metrics explicitly, not be silently accepted as top-level keys."""
    with pytest.raises(ValidationError):
        EnvironmentalState(some_made_up_field="oops")


def test_merge_fills_in_missing_fields_without_losing_existing():
    base = EnvironmentalState(
        region="semi-arid",
        soil=SoilState(organic_carbon_percent=0.3),
    )
    update = EnvironmentalState(
        soil=SoilState(ph=7.8),  # new info, doesn't mention organic_carbon_percent
    )
    merged = base.merge(update)

    assert merged.region == "semi-arid"  # preserved from base
    assert merged.soil.organic_carbon_percent == 0.3  # preserved from base
    assert merged.soil.ph == 7.8  # added from update


def test_merge_prefers_newer_value_on_conflict():
    base = EnvironmentalState(climate={"rainfall_category": "moderate"})
    update = EnvironmentalState(climate={"rainfall_category": "low"})
    merged = base.merge(update)
    assert merged.climate.rainfall_category == "low"


def test_merge_unions_lists_without_duplicating():
    base = EnvironmentalState(biodiversity={"invasive_species": ["lantana"]})
    update = EnvironmentalState(biodiversity={"invasive_species": ["lantana", "water hyacinth"]})
    merged = base.merge(update)
    assert merged.biodiversity.invasive_species == ["lantana", "water hyacinth"]


def test_merge_combines_extra_metrics_dicts():
    base = EnvironmentalState(soil=SoilState(extra_metrics={"a": 1}))
    update = EnvironmentalState(soil=SoilState(extra_metrics={"b": 2}))
    merged = base.merge(update)
    assert merged.soil.extra_metrics == {"a": 1, "b": 2}


def test_demonstration_scenario_constructs_cleanly():
    """The spec's canonical demo input must map onto this schema without
    any special-casing."""
    state = EnvironmentalState(
        region="semi-arid",
        soil=SoilState(organic_carbon_percent=0.3),
        climate={"rainfall_category": "low"},
        land={"crop_type": "wheat", "cropping_system": "monoculture"},
    )
    assert state.soil.organic_carbon_percent == 0.3
    assert state.climate.rainfall_category == "low"
    assert state.land.crop_type == "wheat"
    assert state.land.cropping_system == "monoculture"
