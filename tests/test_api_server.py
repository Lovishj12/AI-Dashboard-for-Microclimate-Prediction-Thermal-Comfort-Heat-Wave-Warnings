"""
Automated unit tests for Phase 8 FastAPI Backend Application.
Uses FastAPI TestClient to test all endpoints:
1. /api/health
2. /api/metadata
3. /api/stations
4. /api/current/{station_id}
5. /api/forecast/{station_id}
6. /api/history/{station_id}
7. /api/psychrometrics/{station_id}
8. /api/calculate (POST)
"""

import unittest
from fastapi.testclient import TestClient
from src.api_server import app

class TestAPIServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("new_delhi", data["available_stations"])

    def test_metadata(self):
        res = self.client.get("/api/metadata")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("standards", data)
        self.assertIn("thresholds", data)

    def test_stations_registry(self):
        res = self.client.get("/api/stations")
        self.assertEqual(res.status_code, 200)
        stations = res.json()
        self.assertEqual(len(stations), 3)
        station_ids = [s["id"] for s in stations]
        self.assertIn("new_delhi", station_ids)
        self.assertIn("kharagpur", station_ids)
        self.assertIn("ahmedabad", station_ids)

    def test_current_conditions(self):
        res = self.client.get("/api/current/new_delhi")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["station_id"], "new_delhi")
        self.assertIn("status", data)
        self.assertIn("thermodynamic_state", data["status"])
        self.assertIn("overall_level", data["status"])

    def test_forecast_endpoint(self):
        res = self.client.get("/api/forecast/new_delhi")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("forecasts", data)
        for h in [1, 3, 6, 24]:
            self.assertIn(f"t_plus_{h}h", data["forecasts"])

    def test_history_endpoint(self):
        res = self.client.get("/api/history/new_delhi?days=3")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["days"], 3)
        self.assertEqual(len(data["series"]), 72)

    def test_psychrometric_chart_data(self):
        res = self.client.get("/api/psychrometrics/new_delhi")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("rh_curves", data)
        self.assertIn("comfort_polygon", data)
        self.assertIn("current_point", data)
        self.assertIn("recent_points", data)
        self.assertGreater(len(data["rh_curves"]["rh_100"]), 0)

    def test_calculate_endpoint(self):
        payload = {
            "temperature_c": 44.0,
            "relative_humidity_pct": 30.0,
            "location_key": "new_delhi"
        }
        res = self.client.post("/api/calculate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("thermodynamic_state", data)
        self.assertIn("overall_level", data)
        self.assertIn("explainability", data)

    def test_invalid_station_404(self):
        res = self.client.get("/api/current/invalid_station_xyz")
        self.assertEqual(res.status_code, 404)

if __name__ == "__main__":
    unittest.main()
