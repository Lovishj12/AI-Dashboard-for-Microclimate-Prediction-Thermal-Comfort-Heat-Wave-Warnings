"""
Automated unit test suite for the Scientific Calculation Engine (Phase 3).
Validates:
1. Physical bounds and thermodynamic laws:
   - T_dp <= T_wb <= T_db (strict psychrometric ordering)
   - When RH = 100%, T_dp == T_wb == T_db (saturation state)
2. Benchmark validation against NOAA NWS Heat Index official calculator values.
3. Stull (2011) Wet-Bulb empirical equation validation against known ground truth.
4. ASHRAE Humidity Ratio and Enthalpy formula correctness.
5. Australian BoM sWBGT calculation correctness.
6. Vectorized DataFrame enrichment on real dataset slices.
"""

import unittest
import numpy as np
import pandas as pd
from src.scientific_engine import (
    saturation_vapor_pressure,
    actual_vapor_pressure,
    dew_point_temperature,
    wet_bulb_temperature,
    humidity_ratio,
    specific_enthalpy,
    heat_index,
    simplified_wbgt,
    classify_heat_index,
    classify_wbgt,
    enrich_meteorological_dataframe,
    STANDARD_PRESSURE_HPA
)

class TestScientificEngine(unittest.TestCase):
    
    def test_saturation_and_vapor_pressure(self):
        # At 0°C, e_s ~ 6.11 hPa
        e_s_0 = saturation_vapor_pressure(0.0)
        self.assertAlmostEqual(e_s_0, 6.112, places=2)
        
        # At 100°C (water boiling), e_s ~ 1013.25 hPa
        e_s_100 = saturation_vapor_pressure(100.0)
        self.assertGreater(e_s_100, 1000.0)
        
        # At 25°C, 50% RH: e_a should be 0.5 * e_s(25)
        e_s_25 = saturation_vapor_pressure(25.0)
        e_a_25 = actual_vapor_pressure(25.0, 50.0)
        self.assertAlmostEqual(e_a_25, 0.5 * e_s_25, places=4)
        
    def test_psychrometric_ordering_and_saturation(self):
        """
        Thermodynamic law: T_dp <= T_wb <= T_db.
        At 100% RH (saturation), T_dp == T_wb == T_db.
        """
        test_temps = [15.0, 25.0, 35.0, 45.0]
        test_rhs = [20.0, 50.0, 80.0]
        
        for t in test_temps:
            for rh in test_rhs:
                dp = dew_point_temperature(t, rh)
                wb = wet_bulb_temperature(t, rh)
                self.assertLessEqual(dp, wb + 0.5, f"Violated dp <= wb for T={t}, RH={rh}")
                self.assertLessEqual(wb, t + 0.5, f"Violated wb <= t for T={t}, RH={rh}")
                
        # Saturation test at 30°C, 100% RH
        dp_sat = dew_point_temperature(30.0, 100.0)
        wb_sat = wet_bulb_temperature(30.0, 100.0)
        self.assertAlmostEqual(dp_sat, 30.0, delta=0.5)
        self.assertAlmostEqual(wb_sat, 30.0, delta=0.5)

    def test_stull_wet_bulb_against_published_benchmark(self):
        """
        Stull (2011) Table 1 validation:
        At T = 20.0°C, RH = 50.0%:
        Stull equation gives Twb ~ 13.7°C.
        """
        twb = wet_bulb_temperature(20.0, 50.0)
        self.assertAlmostEqual(twb, 13.7, delta=0.2)
        
        # At T = 35.0°C, RH = 70.0% (severe heat stress)
        twb_severe = wet_bulb_temperature(35.0, 70.0)
        self.assertAlmostEqual(twb_severe, 30.4, delta=0.4)

    def test_heat_index_against_noaa_nws_benchmarks(self):
        """
        Test NOAA Rothfusz formula against published NWS heat index table:
        1. T = 80°F (26.67°C), RH = 50%: HI should be ~ 80°F (26.67°C)
        2. T = 90°F (32.22°C), RH = 70%: HI should be ~ 106°F (41.11°C) [Danger]
        3. T = 100°F (37.78°C), RH = 60%: HI should be ~ 129°F (53.89°C) [Extreme Danger]
        """
        # Case 1: Moderate
        hi_1 = heat_index(26.6667, 50.0)
        self.assertAlmostEqual(hi_1, 26.67, delta=0.5)
        
        # Case 2: High humidity heat stress (90°F, 70% RH -> 106°F / 41.1°C)
        hi_2 = heat_index(32.2222, 70.0)
        self.assertAlmostEqual(hi_2, 41.1, delta=0.6)
        
        # Case 3: Extreme Danger (100°F, 60% RH -> 129°F / 53.9°C)
        hi_3 = heat_index(37.7778, 60.0)
        self.assertAlmostEqual(hi_3, 53.9, delta=0.8)

    def test_ashrae_humidity_ratio_and_enthalpy(self):
        """
        ASHRAE psychrometric standard state:
        At T = 25°C, P = 1013.25 hPa, RH = 50%:
        T_dp ~ 13.87°C
        e_a ~ 15.84 hPa
        W ~ 0.62198 * 15.84 / (1013.25 - 15.84) ~ 0.00987 kg/kg (9.87 g/kg)
        h ~ 1.006 * 25 + 0.00987 * (2501 + 1.86 * 25) ~ 50.3 kJ/kg
        """
        dp = dew_point_temperature(25.0, 50.0)
        w = humidity_ratio(dp, STANDARD_PRESSURE_HPA)
        self.assertAlmostEqual(w * 1000.0, 9.87, delta=0.3)
        
        h = specific_enthalpy(25.0, w)
        self.assertAlmostEqual(h, 50.3, delta=0.8)

    def test_simplified_wbgt(self):
        """
        BoM formula: sWBGT = 0.567 * T + 0.393 * e_a + 3.94
        At T = 35°C, RH = 60%:
        e_s(35) ~ 56.24 hPa -> e_a = 0.6 * 56.24 = 33.74 hPa
        sWBGT = 0.567 * 35 + 0.393 * 33.74 + 3.94 = 19.845 + 13.260 + 3.94 = 37.04°C
        """
        swbgt = simplified_wbgt(35.0, 60.0)
        self.assertAlmostEqual(swbgt, 37.0, delta=0.3)

    def test_category_classifications(self):
        cat_hi, color_hi = classify_heat_index(42.0)
        self.assertEqual(cat_hi, "Danger")
        
        cat_wbgt, color_wbgt = classify_wbgt(33.0)
        self.assertEqual(cat_wbgt, "Extreme Risk")

    def test_vectorized_dataframe_enrichment(self):
        sample_df = pd.DataFrame({
            "temperature_c": [20.0, 30.0, 42.0, 48.0],
            "relative_humidity_pct": [60.0, 40.0, 25.0, 15.0],
            "surface_pressure_hpa": [1013.25, 1005.0, 995.0, 990.0]
        })
        enriched = enrich_meteorological_dataframe(sample_df)
        
        # Verify all added columns exist
        expected_added_cols = [
            "dew_point_c", "wet_bulb_c", "vapor_pressure_hpa",
            "humidity_ratio_kg_kg", "humidity_ratio_g_kg", "enthalpy_kj_kg",
            "heat_index_c", "swbgt_c"
        ]
        for col in expected_added_cols:
            self.assertIn(col, enriched.columns)
            self.assertEqual(enriched[col].isnull().sum(), 0)
            
        # Monotonicity check on sample
        for _, row in enriched.iterrows():
            self.assertLessEqual(row["dew_point_c"], row["wet_bulb_c"] + 0.5)
            self.assertLessEqual(row["wet_bulb_c"], row["temperature_c"] + 0.5)

if __name__ == "__main__":
    unittest.main()
