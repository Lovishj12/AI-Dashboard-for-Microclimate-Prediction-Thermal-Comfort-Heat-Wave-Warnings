"""
Step 6 Automated Test Suite: Campus-Scale Spatial Microclimate Downscaling Engine.
Validates the physical downscaling logic, campus-wide evaluation, thermodynamic outputs,
and boundary consistency across all 24 landmarks.
"""

from src.campus_microclimate import (
    CampusMicroclimateEngine,
    compute_building_microclimate_delta,
    calculate_vulnerability_index
)

def test_compute_building_microclimate_delta_physics():
    """Verify individual component delta physics."""
    # Cool vegetative zone: high vegetation, low impervious
    cool_zone = compute_building_microclimate_delta(
        albedo=0.35,
        vegetation_fraction=0.75,
        impervious_fraction=0.20,
        sky_view_factor=0.60,
        solar_radiation_wm2=600.0,
        wind_speed_ms=2.0
    )
    # Hot asphalt zone: low albedo, zero vegetation, high impervious
    hot_zone = compute_building_microclimate_delta(
        albedo=0.12,
        vegetation_fraction=0.05,
        impervious_fraction=0.90,
        sky_view_factor=0.85,
        solar_radiation_wm2=600.0,
        wind_speed_ms=2.0
    )

    assert cool_zone["temperature_delta_c"] < 0, "Cool zone must yield negative temperature delta"
    assert hot_zone["temperature_delta_c"] > 0, "Hot zone must yield positive temperature delta"
    assert cool_zone["temperature_delta_c"] < hot_zone["temperature_delta_c"]
    assert "components" in cool_zone
    assert cool_zone["components"]["vegetation_effect"] < 0

def test_vulnerability_index_bounds():
    """Verify Vulnerability Index is properly bounded [0, 100]."""
    score_low = calculate_vulnerability_index(
        heat_index_c=25.0,
        swbgt_c=22.0,
        ac_penetration=1.0,
        footfall="Low",
        baseline_rating="Low"
    )
    score_high = calculate_vulnerability_index(
        heat_index_c=48.0,
        swbgt_c=36.0,
        ac_penetration=0.05,
        footfall="Very High",
        baseline_rating="Extreme"
    )
    
    assert 0.0 <= score_low <= 30.0, f"Expected low score, got {score_low}"
    assert 70.0 <= score_high <= 100.0, f"Expected high score, got {score_high}"

def test_campus_microclimate_engine_all_buildings():
    """Verify evaluation of all 24 campus buildings and summary statistics."""
    engine = CampusMicroclimateEngine()
    result = engine.evaluate_all_buildings(
        regional_temperature_c=38.5,
        regional_relative_humidity_pct=55.0,
        regional_wind_speed_ms=2.5,
        regional_solar_radiation_wm2=650.0
    )

    assert result["tier"] == "Modelled / Estimated (Physics-Downscaled)"
    summary = result["campus_summary"]
    assert summary["total_landmarks"] == 24
    assert summary["thermal_delta_spread_c"] > 0.0
    assert "hottest_building" in summary
    assert "coolest_building" in summary
    
    buildings = result["buildings"]
    assert len(buildings) == 24
    
    # Ensure buildings are sorted by heat index in descending order
    heat_indices = [b["microclimate"]["heat_index_c"] for b in buildings]
    assert heat_indices == sorted(heat_indices, reverse=True), "Buildings should be ranked descending by heat index"

    # Spot check Tikka Lake (wetland) vs Scholars Avenue (asphalt corridor)
    tikka = next(b for b in buildings if b["id"] == "tikka_lake_zone")
    scholars = next(b for b in buildings if b["id"] == "scholars_avenue_junction")
    assert tikka["microclimate"]["temperature_c"] < scholars["microclimate"]["temperature_c"]
