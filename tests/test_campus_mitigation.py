"""
Automated unit tests for Step 13: What-If Mitigation Scenarios & Efficacy Engine.
Validates urban cooling interventions adapted from the UNSW High Performance Architecture Index.
"""

from fastapi.testclient import TestClient
from src.api_server import app

client = TestClient(app)

def test_campus_mitigation_endpoint_status():
    """Verify default intervention query returns 200 with complete academic schema."""
    response = client.get("/api/campus/mitigation")
    assert response.status_code == 200
    data = response.json()
    assert "tier" in data
    assert "intervention" in data
    assert "buildings" in data
    assert len(data["buildings"]) == 24

def test_four_mitigation_interventions():
    """Verify all 4 interventions calculate positive thermodynamic cooling relief."""
    interventions = [
        "cool_roofs",
        "tree_canopy_expansion",
        "permeable_reflective_pavements",
        "comprehensive_green_infrastructure"
    ]
    for iv in interventions:
        res = client.get(f"/api/campus/mitigation?intervention_type={iv}")
        assert res.status_code == 200
        d = res.json()
        assert d["intervention"]["id"] == iv
        assert d["intervention"]["mean_temperature_reduction_c"] > 0
        assert d["intervention"]["mean_heat_index_relief_c"] > 0
        assert d["intervention"]["average_hvac_energy_reduction_pct"] > 0

def test_comprehensive_scenario_efficacy_supremacy():
    """Verify combined comprehensive masterplan provides greater cooling than single interventions."""
    res_cool = client.get("/api/campus/mitigation?intervention_type=cool_roofs").json()
    res_comp = client.get("/api/campus/mitigation?intervention_type=comprehensive_green_infrastructure").json()
    
    cool_reduction = res_cool["intervention"]["mean_temperature_reduction_c"]
    comp_reduction = res_comp["intervention"]["mean_temperature_reduction_c"]
    assert comp_reduction > cool_reduction, f"Comprehensive {comp_reduction} should exceed Cool Roofs {cool_reduction}"

def test_building_cooling_benefits_schema():
    """Verify individual building mitigation payload contains all physical metrics."""
    res = client.get("/api/campus/mitigation?intervention_type=tree_canopy_expansion")
    b0 = res.json()["buildings"][0]
    assert "id" in b0
    assert "unmitigated" in b0
    assert "mitigated" in b0
    assert "net_cooling_benefit" in b0
    benefit = b0["net_cooling_benefit"]
    assert "temperature_reduction_c" in benefit
    assert "heat_index_reduction_c" in benefit
    assert "wet_bulb_reduction_c" in benefit
    assert "vulnerability_points_saved" in benefit
    assert "cooling_degree_hours_saved_pct" in benefit

if __name__ == "__main__":
    test_campus_mitigation_endpoint_status()
    test_four_mitigation_interventions()
    test_comprehensive_scenario_efficacy_supremacy()
    test_building_cooling_benefits_schema()
    print("ALL 4 MITIGATION TESTS PASSED!")
