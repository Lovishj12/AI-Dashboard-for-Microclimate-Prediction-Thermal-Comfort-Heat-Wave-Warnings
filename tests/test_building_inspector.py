"""
Automated Integration Tests for Step 5: Building Selection & Detail Inspector.
Verifies the backend building detail endpoint and downscaled microclimate calculations.
"""

from fastapi.testclient import TestClient
from src.api_server import app

client = TestClient(app)

def test_building_detail_endpoint_success():
    """Verify detail retrieval for Nalanda Classroom Complex."""
    response = client.get("/api/campus/building/nalanda_complex")
    assert response.status_code == 200
    data = response.json()
    
    assert data["building_id"] == "nalanda_complex"
    assert "properties" in data
    assert data["properties"]["name"] == "Nalanda Classroom Complex"
    assert data["properties"]["albedo"] == 0.30
    assert data["properties"]["vegetation_fraction"] == 0.20
    assert data["properties"]["impervious_fraction"] == 0.80
    
    # Check modelled microclimate structure
    micro = data["modelled_microclimate"]
    assert micro["tier"] == "Modelled / Estimated"
    assert "temperature_c" in micro
    assert "temperature_delta_c" in micro
    assert "wet_bulb_c" in micro
    assert "heat_index_c" in micro
    assert "swbgt_c" in micro
    assert "vulnerability_index_score" in micro
    assert 0 <= micro["vulnerability_index_score"] <= 100

def test_building_detail_not_found():
    """Verify 404 response for invalid building id."""
    response = client.get("/api/campus/building/non_existent_building_xyz")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_microclimate_delta_physical_consistency():
    """
    Verify physical behavior:
    Tikka Lake (high veg 0.75, low impervious 0.25) should have lower temperature delta
    than Scholars Avenue (high impervious 0.80, low albedo 0.12).
    """
    res_lake = client.get("/api/campus/building/tikka_lake_zone")
    res_road = client.get("/api/campus/building/scholars_avenue_junction")
    
    assert res_lake.status_code == 200
    assert res_road.status_code == 200
    
    delta_lake = res_lake.json()["modelled_microclimate"]["temperature_delta_c"]
    delta_road = res_road.json()["modelled_microclimate"]["temperature_delta_c"]
    
    # Lake microclimate cooling island vs hot asphalt roadway
    assert delta_lake < delta_road
