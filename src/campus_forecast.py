"""
Step 8: Spatial ML Forecasting Engine at Building Scale for IIT Kharagpur.

Bridges the regional multi-horizon AI/ML champion models (Phases 5-6)
with the physical downscaling engine (Step 6) to produce building-specific
predictive microclimate trajectories for horizons:
- Horizon t+1h: Short-term tactical dispatch
- Horizon t+3h: Intra-day class transitions
- Horizon t+6h: Midday peak exposure warning
- Horizon t+24h: Next-day operational planning

Outputs for each horizon across all 24 buildings:
- Predicted dry-bulb temperature (T_db) & anomaly (ΔT)
- Predicted relative humidity (RH)
- Projected Stull (2011) Wet-Bulb (T_wb)
- Projected NOAA Heat Index (HI) & risk tier
- Projected Simplified WBGT (sWBGT)
- Heat Vulnerability Index (HVI)
- Campus risk ranking & hot-spot alerts
"""

from typing import Dict, List, Any
import pandas as pd
from pathlib import Path

from src.campus_microclimate import CampusMicroclimateEngine
from src.warning_engine import AdvancedWarningEngine

class CampusSpatialForecastEngine:
    """
    Coordinates regional ML forecasting with campus-wide spatial downscaling.
    """

    def __init__(self, warning_engine: AdvancedWarningEngine, microclimate_engine: CampusMicroclimateEngine):
        self.warning_engine = warning_engine
        self.microclimate_engine = microclimate_engine

    def generate_spatial_forecast(
        self,
        recent_slice: pd.DataFrame,
        horizon_hours: int = 1
    ) -> Dict[str, Any]:
        """
        Executes ML inference for a specified horizon (1, 3, 6, 24h) and downscales
        the forecast across all 24 IIT Kharagpur buildings.
        """
        # 1. Run regional ML forecasting for Kharagpur
        regional_multi = self.warning_engine.generate_multi_horizon_forecast("kharagpur", recent_slice)
        
        horizon_key = f"t_plus_{horizon_hours}h"
        if horizon_key not in regional_multi["forecasts"]:
            raise ValueError(f"Horizon {horizon_hours}h not supported. Available: 1, 3, 6, 24")

        reg_fc = regional_multi["forecasts"][horizon_key]
        pred_t = float(reg_fc["predicted_temperature_c"])
        pred_rh = float(reg_fc["predicted_relative_humidity_pct"])
        model_arch = reg_fc["model_architecture"]

        # Approximate diurnal radiation & wind based on horizon
        solar_est = 550.0 if (horizon_hours in [1, 3, 6]) else 400.0
        wind_est = 2.2

        # 2. Downscale regional forecast to all 24 buildings
        downscaled = self.microclimate_engine.evaluate_all_buildings(
            regional_temperature_c=pred_t,
            regional_relative_humidity_pct=pred_rh,
            regional_wind_speed_ms=wind_est,
            regional_solar_radiation_wm2=solar_est
        )

        return {
            "tier": "Predicted / Modelled (AI Forecast + Physical Downscaling)",
            "horizon_hours": horizon_hours,
            "horizon_label": f"t+{horizon_hours}h",
            "model_architecture": model_arch,
            "regional_forecast": {
                "station": "Kharagpur Station (Regional AI Forecast)",
                "predicted_temperature_c": pred_t,
                "predicted_relative_humidity_pct": pred_rh,
                "warning_level": reg_fc["warning_level"],
                "warning_color": reg_fc["warning_color"]
            },
            "campus_summary": downscaled["campus_summary"],
            "buildings": downscaled["buildings"]
        }

    def generate_all_horizons_spatial_forecast(
        self,
        recent_slice: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Generates full multi-horizon forecast (1, 3, 6, 24h) for the entire campus.
        """
        horizons = [1, 3, 6, 24]
        results = {}
        for h in horizons:
            results[f"t_plus_{h}h"] = self.generate_spatial_forecast(recent_slice, horizon_hours=h)

        return {
            "tier": "Predicted / Modelled (AI Forecast + Physical Downscaling)",
            "horizons": results
        }
