"""
Unit tests for Phase 2 Data Pipeline.
Validates:
1. Config loading
2. Data continuity and index monotonicity
3. Non-null assertions on core variables
4. Physical plausibility bounds (temperature, humidity, wind, pressure, solar radiation)
"""

import unittest
from pathlib import Path
import pandas as pd
from src.config import load_config

class TestDataPipeline(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.processed_dir = Path(self.config["data_pipeline"]["processed_dir"])
        self.locations = list(self.config["locations"].keys())
        
    def test_config_structure(self):
        self.assertIn("locations", self.config)
        self.assertIn("data_pipeline", self.config)
        self.assertIn("kharagpur", self.locations)
        self.assertEqual(len(self.locations), 1)
        
    def test_datasets_exist(self):
        for loc in self.locations:
            csv_path = self.processed_dir / f"{loc}_hourly.csv"
            self.assertTrue(csv_path.exists(), f"Missing dataset: {csv_path}")
            
    def test_data_integrity_and_physical_bounds(self):
        for loc in self.locations:
            csv_path = self.processed_dir / f"{loc}_hourly.csv"
            df = pd.read_csv(csv_path, index_col="timestamp_utc", parse_dates=True)
            
            # 1. Row count check (18 months hourly = ~13,128 rows)
            self.assertGreaterEqual(len(df), 13000, f"Insufficient records for {loc}")
            
            # 2. Index strictly increasing with uniform hourly frequency
            self.assertTrue(df.index.is_monotonic_increasing, f"Index not monotonic for {loc}")
            self.assertFalse(df.index.has_duplicates, f"Duplicate timestamps found in {loc}")
            
            # 3. Essential columns present
            expected_cols = [
                "temperature_c", "relative_humidity_pct", "wind_speed_ms",
                "surface_pressure_hpa", "solar_radiation_wm2", "location"
            ]
            for col in expected_cols:
                self.assertIn(col, df.columns, f"Missing column {col} in {loc}")
                self.assertEqual(df[col].isnull().sum(), 0, f"Nulls found in {col} for {loc}")
                
            # 4. Physical Plausibility Sanity Bounds
            # Temperature: -10°C to 55°C for Indian stations
            self.assertTrue((df["temperature_c"] >= -10.0).all() and (df["temperature_c"] <= 55.0).all())
            
            # Relative Humidity: 0% to 100%
            self.assertTrue((df["relative_humidity_pct"] >= 0.0).all() and (df["relative_humidity_pct"] <= 100.0).all())
            
            # Wind speed: >= 0 m/s and < 60 m/s
            self.assertTrue((df["wind_speed_ms"] >= 0.0).all() and (df["wind_speed_ms"] < 60.0).all())
            
            # Surface pressure: 850 hPa to 1050 hPa
            self.assertTrue((df["surface_pressure_hpa"] >= 850.0).all() and (df["surface_pressure_hpa"] <= 1050.0).all())
            
            # Solar radiation: >= 0 W/m^2 and <= 1500 W/m^2
            self.assertTrue((df["solar_radiation_wm2"] >= 0.0).all() and (df["solar_radiation_wm2"] <= 1500.0).all())

if __name__ == "__main__":
    unittest.main()
