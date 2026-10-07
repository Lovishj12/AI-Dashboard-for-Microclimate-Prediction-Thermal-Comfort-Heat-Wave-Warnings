"""
Step 11 Automated Integration Tests: Heat Wave & Extreme Event Scenario Stress Testing.
Validates the thermodynamic response of all 24 campus buildings to IMD Heat Wave scenarios,
critical wet-bulb threshold audits, and institutional emergency directives.
"""

from fastapi.testclient import TestClient
from src.api_server import app

client = TestClient(app)

def test_heat_wave_scenario_defaults():
    """Verify default IMD severe heat wave scenario evaluation."""
    response = client.get("/api/campus/heatwave")
    assert response.status_code == 200
    data = response.json()
    
    assert data["tier"] == "Modelled / Scenario Simulation (Heat Wave Stress Test)"
    assert "scenario" in data
    assert "stress_test_audit" in data
    assert "buildings" in data
    assert len(data["buildings"]) == 24
    
    audit = data["stress_test_audit"]
    assert "critical_twb_count" in audit
    assert "extreme_danger_hi_count" in audit
    assert "institutional_action" in audit
    assert 0 <= audit["critical_twb_count"] <= 24

def test_heat_wave_scenario_types():
    """Verify all 4 standardized heat wave stress-test scenarios."""
    scenarios = ["imd_heat_wave", "imd_severe_heat_wave", "humid_heat_crisis", "dry_convective_blast"]
    
    for sc in scenarios:
        res = client.get(f"/api/campus/heatwave?scenario_type={sc}")
        assert res.status_code == 200
        data = res.json()
        assert data["scenario"]["id"] == sc
        assert data["scenario"]["regional_temperature_c"] > 30.0
        assert len(data["buildings"]) == 24

def test_heat_wave_physical_amplification():
    """Verify that IMD severe heat wave (+6.5°C) yields higher thermal stress than standard (+4.5°C)."""
    res_std = client.get("/api/campus/heatwave?scenario_type=imd_heat_wave").json()
    res_sev = client.get("/api/campus/heatwave?scenario_type=imd_severe_heat_wave").json()
    
    t_std = res_std["scenario"]["regional_temperature_c"]
    t_sev = res_sev["scenario"]["regional_temperature_c"]
    assert t_sev > t_std, "Severe heat wave must have higher forcing temperature"
    
    hi_std = res_std["campus_summary"]["hottest_building"]["heat_index_c"]
    hi_sev = res_sev["campus_summary"]["hottest_building"]["heat_index_c"]
    assert hi_sev >= hi_std, "Severe heat wave must yield higher or equal maximum Heat Index"
