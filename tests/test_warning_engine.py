"""
Automated unit tests for Phase 7 Advanced Warning System.
Validates:
1. IMD heat-wave criteria logic (normal departures and absolute thresholds).
2. Comprehensive multi-tier warning synthesis across normal, heat-wave, and emergency states.
3. Multi-horizon forecasting integration with real historical input data slices.
4. Output schema completeness and explainability presence.
"""

import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from src.warning_engine import AdvancedWarningEngine
from src.config import load_config

class TestWarningEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        cls.engine = AdvancedWarningEngine(cls.config)
        
        # Load a recent slice of Kharagpur data for testing forecasts
        csv_path = Path(cls.config["data_pipeline"]["processed_dir"]) / "enriched" / "kharagpur_enriched_hourly.csv"
        cls.df = pd.read_csv(csv_path, index_col="timestamp_utc", parse_dates=True)

    def test_imd_heat_wave_classification(self):
        # 1. Normal day in Kharagpur (T = 35°C)
        res_normal = self.engine.evaluate_imd_heat_wave_status("kharagpur", 35.0, month=5)
        self.assertEqual(res_normal["status"], "No Heat Wave")
        self.assertEqual(res_normal["severity_rank"], 0)
        
        # 2. Heat wave by departure (Kharagpur normal = 37.1°C, test at 42.0°C -> departure = +4.9°C)
        res_hw = self.engine.evaluate_imd_heat_wave_status("kharagpur", 42.0, month=5)
        self.assertEqual(res_hw["status"], "Heat Wave")
        self.assertGreaterEqual(res_hw["severity_rank"], 2)
        
        # 3. Severe heat wave by absolute criteria (T = 47.0°C)
        res_severe = self.engine.evaluate_imd_heat_wave_status("kharagpur", 47.0, month=5)
        self.assertEqual(res_severe["status"], "Severe Heat Wave")
        self.assertEqual(res_severe["severity_rank"], 3)

    def test_comprehensive_warning_synthesis(self):
        # Benign state: 25°C, 45% RH
        w_benign = self.engine.generate_comprehensive_warning(25.0, 45.0, "kharagpur")
        self.assertEqual(w_benign["overall_level"], "NORMAL")
        self.assertEqual(w_benign["overall_color"], "#2ecc71")
        self.assertIn("thermodynamic_state", w_benign)
        
        # Danger state: 41°C, 35% RH (HI ~ 48°C)
        w_danger = self.engine.generate_comprehensive_warning(41.0, 35.0, "kharagpur")
        self.assertIn(w_danger["overall_level"], ["DANGER", "EXTREME DANGER", "CRITICAL EMERGENCY"])
        self.assertGreater(len(w_danger["explainability"]["primary_triggers"]), 0)
        self.assertGreater(len(w_danger["explainability"]["action_recommendations"]), 0)

    def test_multi_horizon_forecast_pipeline(self):
        # Feed 48 hours of real historical data into forecast engine
        test_window = self.df.iloc[-48:]
        forecast_res = self.engine.generate_multi_horizon_forecast("kharagpur", test_window)
        
        self.assertEqual(forecast_res["location"], "kharagpur")
        self.assertIn("current_status", forecast_res)
        self.assertIn("forecasts", forecast_res)
        
        # Verify all horizons present
        for h in [1, 3, 6, 24]:
            key = f"t_plus_{h}h"
            self.assertIn(key, forecast_res["forecasts"])
            h_data = forecast_res["forecasts"][key]
            self.assertIn("predicted_temperature_c", h_data)
            self.assertIn("warning_level", h_data)
            self.assertTrue(np.isfinite(h_data["predicted_temperature_c"]))

if __name__ == "__main__":
    unittest.main()
