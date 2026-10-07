"""
Step 10 Automated Integration Tests: Diurnal Microclimatic Cycle Simulation.
Verifies the physics of 24-hour diurnal evolution across all 24 campus buildings.
"""

from fastapi.testclient import TestClient
from src.api_server import app

client = TestClient(app)

def test_diurnal_endpoint_structure():
    """Verify 24-hour diurnal trajectory structure."""
    response = client.get("/api/campus/diurnal")
    assert response.status_code == 200
    timeline = response.json()
    
    assert len(timeline) == 24, "Diurnal simulation must produce exactly 24 hourly steps"
    
    # Check hour 00 and hour 12 steps
    h0 = timeline[0]
    h12 = timeline[12]
    
    assert h0["hour"] == 0
    assert h0["hour_label"] == "00:00"
    assert h0["solar_radiation_wm2"] == 0.0, "Nighttime radiation must be zero"
    assert len(h0["buildings"]) == 24
    
    assert h12["hour"] == 12
    assert h12["hour_label"] == "12:00"
    assert h12["solar_radiation_wm2"] > 500.0, "Midday solar radiation must be high"
    assert len(h12["buildings"]) == 24

def test_diurnal_thermodynamic_physics():
    """Verify physical diurnal properties: Midday temperature > Midnight temperature."""
    response = client.get("/api/campus/diurnal")
    timeline = response.json()
    
    t_midnight = timeline[0]["regional_reference"]["temperature_c"]
    t_afternoon = timeline[14]["regional_reference"]["temperature_c"] # peak at 14:00
    
    assert t_afternoon > t_midnight, "Afternoon temperature must exceed midnight temperature"
    
    # Check diurnal campus thermal spread
    spread_afternoon = timeline[14]["campus_summary"]["thermal_delta_spread_c"]
    assert spread_afternoon > 0.0, "Campus microclimate thermal spread must be non-zero"
