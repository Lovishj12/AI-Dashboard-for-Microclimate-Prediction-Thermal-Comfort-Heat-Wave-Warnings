"""
Step 8 Automated Test Suite: Spatial ML Forecasting Engine at Building Scale.
Verifies multi-horizon regional AI inference coupling with campus spatial downscaling.
"""

from fastapi.testclient import TestClient
from src.api_server import app

client = TestClient(app)

def test_spatial_forecast_all_horizons():
    """Verify campus forecast for all horizons (t+1h, t+3h, t+6h, t+24h)."""
    response = client.get("/api/campus/forecast")
    assert response.status_code == 200
    data = response.json()
    
    assert data["tier"] == "Predicted / Modelled (AI Forecast + Physical Downscaling)"
    assert "horizons" in data
    
    for h in [1, 3, 6, 24]:
        h_key = f"t_plus_{h}h"
        assert h_key in data["horizons"]
        fc = data["horizons"][h_key]
        assert fc["horizon_hours"] == h
        assert len(fc["buildings"]) == 24
        assert "model_architecture" in fc
        assert "campus_summary" in fc

def test_spatial_forecast_single_horizon():
    """Verify single-horizon spatial prediction endpoint."""
    response = client.get("/api/campus/forecast/6")
    assert response.status_code == 200
    data = response.json()
    
    assert data["horizon_hours"] == 6
    assert data["horizon_label"] == "t+6h"
    assert len(data["buildings"]) == 24
    
    # Check physical values in prediction
    first_b = data["buildings"][0]
    micro = first_b["microclimate"]
    assert "temperature_c" in micro
    assert "heat_index_c" in micro
    assert "wet_bulb_c" in micro
    assert "vulnerability_score" in micro

def test_spatial_forecast_invalid_horizon():
    """Verify error handling for invalid horizon."""
    response = client.get("/api/campus/forecast/12")
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()
