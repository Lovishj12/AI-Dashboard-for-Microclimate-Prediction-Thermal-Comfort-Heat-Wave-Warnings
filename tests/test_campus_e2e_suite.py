"""
Step 14: Comprehensive End-to-End Testing & Academic Validation Suite.
IIT Kharagpur Campus-Scale Microclimate Mapping & Heat-Risk Decision-Support System.
BTP Thesis Verification Suite under Prof. Chirodeep Bakli, IIT Kharagpur.

Validates all 13 integrated campus-scale components:
1. Spatial GeoJSON integrity & 24 campus landmarks (Step 2 & 3)
2. Building inventory API & attribute consistency (Step 4)
3. Individual building inspector & envelope physics (Step 5)
4. Empirical microclimate downscaling engine (Step 6)
5. Multi-horizon spatial machine learning forecasting (Step 8)
6. 24-hour diurnal cycle simulation & solar cycle physics (Step 10)
7. Extreme heat wave stress-testing scenarios & IMD thresholds (Step 11)
8. Multi-dimensional campus vulnerability & HVI ranking (Steps 9 & 12)
9. What-if urban cooling mitigation scenarios (Step 13)
10. Academic integrity tier labeling across all endpoints
11. Regional baseline weather continuity (Phases 1-9 preservation)
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient
from src.api_server import app
import json

client = TestClient(app)

def test_01_spatial_geojson_dataset():
    """Verify GeoJSON dataset integrity: 24 features, WGS84 coordinates in IIT Kharagpur bounds."""
    geojson_path = Path("data/iit_kgp_campus.geojson")
    assert geojson_path.exists(), "Campus GeoJSON file missing!"
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("type") == "FeatureCollection"
    features = data.get("features", [])
    assert len(features) == 24, f"Expected 24 landmarks, got {len(features)}"

    # Coordinate bounding box check for IIT Kharagpur (Lat 22.30 to 22.34, Lon 87.28 to 87.33)
    for feat in features:
        props = feat["properties"]
        geom = feat["geometry"]
        assert "id" in props and "name" in props and "category" in props
        assert geom["type"] == "Polygon"
        coords = geom["coordinates"][0]
        assert coords[0] == coords[-1], f"Polygon not closed for {props['name']}"
        lat = props["latitude"]
        lon = props["longitude"]
        assert 87.295 <= lon <= 87.325, f"Longitude {lon} out of campus bounds for {props['name']}"
        assert 22.305 <= lat <= 22.330, f"Latitude {lat} out of campus bounds for {props['name']}"

def test_02_campus_buildings_endpoint():
    """Verify GET /api/campus/buildings returns complete building inventory."""
    res = client.get("/api/campus/buildings")
    assert res.status_code == 200
    data = res.json()
    assert data.get("type") == "FeatureCollection"
    assert "campus_metadata" in data
    assert data["campus_metadata"]["total_features"] == 24
    assert len(data["features"]) == 24
    assert "Indian Institute of Technology Kharagpur" in data["campus_metadata"]["institution"]

def test_03_building_inspector_physics():
    """Verify GET /api/campus/building/{id} computes physics-based cooling/heating penalties."""
    # Test high-thermal-mass building (Nalanda)
    res_nalanda = client.get("/api/campus/building/nalanda_complex")
    assert res_nalanda.status_code == 200
    d_nalanda = res_nalanda.json()
    assert "building_id" in d_nalanda
    assert "modelled_microclimate" in d_nalanda
    assert "tier" in d_nalanda["modelled_microclimate"]
    assert "Modelled" in d_nalanda["modelled_microclimate"]["tier"]

    # Test lake water-body evaporative cooling
    res_lake = client.get("/api/campus/building/tikka_lake_zone")
    assert res_lake.status_code == 200
    d_lake = res_lake.json()
    lake_delta_t = d_lake["modelled_microclimate"]["temperature_delta_c"]
    nalanda_delta_t = d_nalanda["modelled_microclimate"]["temperature_delta_c"]
    assert lake_delta_t < nalanda_delta_t, f"Lake ({lake_delta_t}) should be cooler than Nalanda ({nalanda_delta_t})"

def test_04_spatial_microclimate_downscaling():
    """Verify GET /api/campus/microclimate/current computes downscaled states for all 24 landmarks."""
    res = client.get("/api/campus/microclimate/current")
    assert res.status_code == 200
    data = res.json()
    assert "regional_reference" in data
    assert "campus_summary" in data
    assert "buildings" in data
    assert len(data["buildings"]) == 24

    summary = data["campus_summary"]
    assert summary["hottest_building"]["temperature_c"] >= summary["coolest_building"]["temperature_c"]
    assert summary["thermal_delta_spread_c"] >= 0.0

def test_05_multi_horizon_spatial_forecasting():
    """Verify ML-driven spatial forecast downscaling across champion horizons 1h, 3h, 6h, 24h."""
    for horizon in [1, 3, 6, 24]:
        res = client.get(f"/api/campus/forecast/{horizon}")
        assert res.status_code == 200
        data = res.json()
        assert data["horizon_hours"] == horizon
        assert len(data["buildings"]) == 24
        assert "predicted_temperature_c" in data["regional_forecast"]

    # Verify invalid horizon validation
    res_bad = client.get("/api/campus/forecast/12")
    assert res_bad.status_code == 400

def test_06_diurnal_24h_cycle_physics():
    """Verify GET /api/campus/diurnal models solar cycle with afternoon peak exceeding midnight."""
    res = client.get("/api/campus/diurnal")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 24

    t_midnight = data[0]["regional_reference"]["temperature_c"]
    t_afternoon = data[14]["regional_reference"]["temperature_c"]
    assert t_afternoon > t_midnight, f"Afternoon ({t_afternoon}) must exceed midnight ({t_midnight})"
    assert data[14]["is_daylight"] is True
    assert data[2]["is_daylight"] is False
    assert data[14]["campus_summary"]["thermal_delta_spread_c"] > 0.0

def test_07_extreme_heat_wave_stress_scenarios():
    """Verify GET /api/campus/heatwave stresses campus across IMD heat wave tiers."""
    scenarios = ["imd_heat_wave", "imd_severe_heat_wave", "humid_heat_crisis", "dry_convective_blast"]
    for sc in scenarios:
        res = client.get(f"/api/campus/heatwave?scenario_type={sc}")
        assert res.status_code == 200
        data = res.json()
        assert data["scenario"]["id"] == sc
        assert data["scenario"]["regional_temperature_c"] > 30.0
        assert "campus_summary" in data
        assert "stress_test_audit" in data
        assert len(data["buildings"]) == 24

    # Verify physical amplification: Severe Heat Wave > Standard Heat Wave
    res_std = client.get("/api/campus/heatwave?scenario_type=imd_heat_wave").json()
    res_sev = client.get("/api/campus/heatwave?scenario_type=imd_severe_heat_wave").json()
    assert res_sev["scenario"]["regional_temperature_c"] > res_std["scenario"]["regional_temperature_c"]
    assert res_sev["campus_summary"]["hottest_building"]["temperature_c"] > res_std["campus_summary"]["hottest_building"]["temperature_c"]

def test_08_campus_vulnerability_layer():
    """Verify GET /api/campus/vulnerability evaluates HVI with AC penetration and footfall weighting."""
    res = client.get("/api/campus/vulnerability")
    assert res.status_code == 200
    data = res.json()
    assert "total_precincts" in data
    assert data["total_precincts"] == 24
    assert "precincts" in data
    assert len(data["precincts"]) == 24

    # Verification of composite vulnerability ordering
    precincts = data["precincts"]
    assert precincts[0]["composite_vulnerability_index"] >= precincts[-1]["composite_vulnerability_index"]
    assert "vulnerability_tier" in precincts[0]
    assert "directive" in precincts[0]

def test_09_what_if_mitigation_engine():
    """Verify GET /api/campus/mitigation computes thermodynamic cooling relief across 4 strategies."""
    strategies = [
        "cool_roofs",
        "tree_canopy_expansion",
        "permeable_reflective_pavements",
        "comprehensive_green_infrastructure"
    ]
    for strat in strategies:
        res = client.get(f"/api/campus/mitigation?intervention_type={strat}")
        assert res.status_code == 200
        data = res.json()
        assert data["intervention"]["mean_temperature_reduction_c"] > 0
        assert data["intervention"]["mean_heat_index_relief_c"] > 0
        assert data["intervention"]["average_hvac_energy_reduction_pct"] > 0

def test_10_academic_tier_labeling():
    """Verify all campus microclimate and forecasting endpoints explicitly declare academic tier."""
    endpoints = [
        "/api/campus/microclimate/current",
        "/api/campus/forecast/3",
        "/api/campus/heatwave",
        "/api/campus/vulnerability",
        "/api/campus/mitigation"
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200
        data = res.json()
        assert "tier" in data, f"Endpoint {ep} missing academic 'tier' attribute!"
        tier_str = data["tier"]
        assert any(keyword in tier_str for keyword in ["Ground-Truth", "Modelled", "Simulation", "Index"]), \
            f"Endpoint {ep} has improper tier: {tier_str}"

    # Verify diurnal cycle steps declare academic tier
    res_diurnal = client.get("/api/campus/diurnal")
    assert res_diurnal.status_code == 200
    assert "tier" in res_diurnal.json()[0]

    # Also verify building inspector contains tier in modelled_microclimate
    res_b = client.get("/api/campus/building/nalanda_complex")
    assert res_b.status_code == 200
    assert "tier" in res_b.json()["modelled_microclimate"]

def test_11_preservation_of_phases_1_to_9():
    """Verify original baseline weather, psychrometric, forecast, and history endpoints remain functional."""
    # 1. Weather station registry
    res_st = client.get("/api/stations")
    assert res_st.status_code == 200
    stations = res_st.json()
    assert len(stations) >= 3
    station_ids = [s["id"] for s in stations]
    assert "kharagpur" in station_ids
    assert "new_delhi" in station_ids

    # 2. Psychrometrics
    res_psy = client.get("/api/psychrometrics/new_delhi")
    assert res_psy.status_code == 200
    assert "rh_curves" in res_psy.json()

    # 3. Custom Calculator
    res_calc = client.post("/api/calculate", json={
        "temperature_c": 42.5,
        "relative_humidity_pct": 55.0,
        "location_key": "kharagpur"
    })
    assert res_calc.status_code == 200
    d_calc = res_calc.json()
    assert "thermodynamic_state" in d_calc
    assert "overall_level" in d_calc

def run_all_e2e_tests():
    print("=" * 80)
    print("RUNNING IIT KHARAGPUR BTP CAMPUS MICROCLIMATE END-TO-END VALIDATION SUITE")
    print("=" * 80)
    tests = [
        ("Test 01: Spatial GeoJSON Dataset (24 Landmarks & Bounds)", test_01_spatial_geojson_dataset),
        ("Test 02: Campus Building Inventory API", test_02_campus_buildings_endpoint),
        ("Test 03: Building Inspector Envelope Thermodynamics", test_03_building_inspector_physics),
        ("Test 04: Spatial Microclimate Downscaling Engine", test_04_spatial_microclimate_downscaling),
        ("Test 05: Multi-Horizon ML Spatial Forecasting", test_05_multi_horizon_spatial_forecasting),
        ("Test 06: Diurnal 24-Hour Solar Cycle Physics", test_06_diurnal_24h_cycle_physics),
        ("Test 07: Extreme Heat Wave Stress Testing (IMD Thresholds)", test_07_extreme_heat_wave_stress_scenarios),
        ("Test 08: Multi-Dimensional Campus Vulnerability Layer", test_08_campus_vulnerability_layer),
        ("Test 09: What-If Urban Cooling Mitigation Engine (UNSW Index)", test_09_what_if_mitigation_engine),
        ("Test 10: Academic Integrity Tier Labeling on All Endpoints", test_10_academic_tier_labeling),
        ("Test 11: Preservation of Phases 1-9 Core Engine & Visualizers", test_11_preservation_of_phases_1_to_9),
    ]

    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS: {name}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {name} -> Error: {e}")
            raise e

    print("=" * 80)
    print(f"E2E SUITE RESULT: ALL {passed}/{len(tests)} TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_all_e2e_tests()
