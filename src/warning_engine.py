"""
Advanced Warning System & Multi-Horizon Forecast Engine (Phase 7).
Integrates:
1. Current environmental observations (T_db, RH, WS, Solar, Pressure).
2. Scientific thermodynamic state calculations (T_wb, T_dp, W, Enthalpy, Heat Index, sWBGT).
3. AI/ML Champion multi-horizon forecasting (h in {1, 3, 6, 24 hours}).
4. Official Multi-Tier Warning Rule Engines:
   - IMD Heat Wave Rules (Climatological normal departure & absolute thresholds).
   - NOAA/NWS Heat Index Alert Levels (Normal, Caution, Extreme Caution, Danger, Extreme Danger).
   - OSHA / ISO 7243 WBGT Occupational Risk Levels (Low, Moderate, High, Extreme).
   - Physiological Critical Wet-Bulb Warning (Twb >= 30°C Severe, >= 35°C Lethal).
5. Explainability & Traceability Generator:
   - Human-interpretable rationale detailing which parameters and thresholds triggered the warning.
   - Recommended actions for general public, municipal authorities, and outdoor workers.
"""

from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any

from src.config import load_config
from src.scientific_engine import (
    dew_point_temperature,
    wet_bulb_temperature,
    actual_vapor_pressure,
    humidity_ratio,
    specific_enthalpy,
    heat_index,
    simplified_wbgt,
    classify_heat_index,
    classify_wbgt,
    STANDARD_PRESSURE_HPA
)
from src.baseline_model import create_time_series_features

CHAMPION_MODELS_DIR = Path("models/champion")

class AdvancedWarningEngine:
    """
    Core warning and forecasting engine combining physical thermodynamics,
    AI inference, and official meteorological guidelines.
    """
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or load_config()
        self.locations = self.config["locations"]
        self.thresholds = self.config["warning_thresholds"]
        self._loaded_models = {}

    def _get_champion_model(self, location_key: str, horizon: int) -> Dict[str, Any]:
        """Lazy loader for serialized champion model artifacts."""
        cache_key = f"{location_key}_h{horizon}"
        if cache_key not in self._loaded_models:
            model_path = CHAMPION_MODELS_DIR / f"{location_key}_champion_h{horizon}.joblib"
            if not model_path.exists():
                raise FileNotFoundError(f"Champion model artifact not found: {model_path}")
            self._loaded_models[cache_key] = joblib.load(model_path)
        return self._loaded_models[cache_key]

    def evaluate_imd_heat_wave_status(
        self,
        location_key: str,
        current_t_max: float,
        month: int = 5
    ) -> Dict[str, Any]:
        """
        Evaluates current or predicted temperature against official IMD heat-wave criteria:
        1. Base threshold for plains: T_max >= 40.0°C.
        2. Absolute Criteria:
           - Heat Wave: T_max >= 45.0°C
           - Severe Heat Wave: T_max >= 47.0°C
        3. Departure from Normal Criteria:
           - Normal climatology loaded from config (e.g. May/June Safdarjung normal).
           - Departure 4.5°C to 6.4°C: Heat Wave
           - Departure > 6.4°C: Severe Heat Wave
        """
        loc_cfg = self.locations.get(location_key, {})
        base_t = self.thresholds["imd"]["plains_base_t_max"]
        
        # Determine applicable climatological normal
        if month == 6 and "imd_normal_max_t_june" in loc_cfg:
            normal_t = loc_cfg["imd_normal_max_t_june"]
        else:
            normal_t = loc_cfg.get("imd_normal_max_t_may", 40.0)
            
        departure = current_t_max - normal_t
        is_heat_wave = False
        is_severe = False
        reasons = []

        if current_t_max >= base_t:
            # Check absolute threshold
            if current_t_max >= self.thresholds["imd"]["heat_wave_absolute_severe"]:
                is_severe = True
                reasons.append(f"Absolute max temp ({current_t_max:.1f}°C) exceeds IMD Severe Heat Wave threshold (≥47.0°C)")
            elif current_t_max >= self.thresholds["imd"]["heat_wave_absolute_min"]:
                is_heat_wave = True
                reasons.append(f"Absolute max temp ({current_t_max:.1f}°C) exceeds IMD Heat Wave threshold (≥45.0°C)")
                
            # Check departure threshold
            if departure > self.thresholds["imd"]["heat_wave_departure_severe"]:
                is_severe = True
                reasons.append(f"Temperature departure (+{departure:.1f}°C) exceeds Severe Heat Wave normal (+6.4°C above {normal_t}°C)")
            elif departure >= self.thresholds["imd"]["heat_wave_departure_min"]:
                is_heat_wave = True
                reasons.append(f"Temperature departure (+{departure:.1f}°C) exceeds Heat Wave normal (+4.5°C above {normal_t}°C)")
        else:
            reasons.append(f"Max temp ({current_t_max:.1f}°C) below IMD plains base threshold ({base_t}°C)")

        if is_severe:
            status = "Severe Heat Wave"
            alert_color = "#900c3f"  # Maroon / Red
            severity_rank = 3
        elif is_heat_wave:
            status = "Heat Wave"
            alert_color = "#e74c3c"  # Red
            severity_rank = 2
        else:
            status = "No Heat Wave"
            alert_color = "#27ae60"  # Green
            severity_rank = 0

        return {
            "status": status,
            "severity_rank": severity_rank,
            "alert_color": alert_color,
            "current_max_t": round(current_t_max, 1),
            "climatological_normal_t": round(normal_t, 1),
            "departure_c": round(departure, 1),
            "reasons": reasons
        }

    def generate_comprehensive_warning(
        self,
        temperature_c: float,
        relative_humidity_pct: float,
        location_key: str,
        wind_speed_ms: float = 2.0,
        surface_pressure_hpa: float = STANDARD_PRESSURE_HPA,
        solar_radiation_wm2: float = 0.0,
        is_forecast: bool = False,
        horizon_hours: int = 0
    ) -> Dict[str, Any]:
        """
        Evaluates physical parameters through all thermodynamic and meteorological warning tiers,
        synthesizing an overall alert level with explainability and actionable guidance.
        """
        # 1. Physical Calculations
        t_dp = float(dew_point_temperature(temperature_c, relative_humidity_pct))
        t_wb = float(wet_bulb_temperature(temperature_c, relative_humidity_pct))
        hi = float(heat_index(temperature_c, relative_humidity_pct))
        swbgt = float(simplified_wbgt(temperature_c, relative_humidity_pct))
        w_ratio = float(humidity_ratio(t_dp, surface_pressure_hpa) * 1000.0)  # g/kg
        enthalpy = float(specific_enthalpy(temperature_c, w_ratio / 1000.0))

        # 2. Risk Classifications
        hi_category, hi_color = classify_heat_index(hi)
        wbgt_category, wbgt_color = classify_wbgt(swbgt)
        imd_eval = self.evaluate_imd_heat_wave_status(location_key, temperature_c)

        # 3. Critical Wet-Bulb Physiological Strain Check
        twb_critical = False
        twb_reason = None
        if t_wb >= 35.0:
            twb_critical = True
            twb_reason = f"CRITICAL LETHAL LIMIT: Wet-Bulb ({t_wb:.1f}°C) ≥ 35°C. Evaporative cooling mathematically impossible."
        elif t_wb >= 30.0:
            twb_critical = True
            twb_reason = f"SEVERE PHYSIOLOGICAL STRAIN: Wet-Bulb ({t_wb:.1f}°C) ≥ 30°C. Perspiration cooling severely impaired."

        # 4. Synthesize Overall Alert Level
        # Hierarchy: Critical Wet-Bulb > Severe Heat Wave / Extreme Danger HI > Heat Wave / Danger HI > Extreme Caution > Caution > Normal
        triggers = []
        action_recommendations = []

        if twb_critical:
            overall_level = "CRITICAL EMERGENCY"
            overall_color = "#512e5f"
            triggers.append(twb_reason)
            action_recommendations.extend([
                "Immediate indoor shelter with air conditioning required.",
                "Halt all physical exertion and outdoor labor.",
                "Provide active cooling (ice baths, mist fans) for exposed individuals."
            ])
        elif imd_eval["status"] == "Severe Heat Wave" or hi_category == "Extreme Danger":
            overall_level = "EXTREME DANGER"
            overall_color = "#900c3f"
            if imd_eval["status"] == "Severe Heat Wave":
                triggers.extend(imd_eval["reasons"])
            if hi_category == "Extreme Danger":
                triggers.append(f"NOAA Heat Index ({hi:.1f}°C) in Extreme Danger category (≥51°C)")
            action_recommendations.extend([
                "Heat stroke imminent with continued outdoor exposure.",
                "Enforce shutdown of outdoor construction and sports between 11:00 and 16:00.",
                "Municipalities should open public cooling shelters and supply drinking water."
            ])
        elif imd_eval["status"] == "Heat Wave" or hi_category == "Danger" or wbgt_category == "Extreme Risk":
            overall_level = "DANGER"
            overall_color = "#e74c3c"
            if imd_eval["status"] == "Heat Wave":
                triggers.extend(imd_eval["reasons"])
            if hi_category == "Danger":
                triggers.append(f"NOAA Heat Index ({hi:.1f}°C) in Danger zone (39°C - 51°C)")
            if wbgt_category == "Extreme Risk":
                triggers.append(f"Simplified WBGT ({swbgt:.1f}°C) in Extreme Risk zone (≥32.2°C)")
            action_recommendations.extend([
                "High probability of heat cramps and heat exhaustion.",
                "Mandatory 15-minute rest breaks per hour for outdoor workers.",
                "Stay hydrated and avoid direct sunlight during midday hours."
            ])
        elif hi_category == "Extreme Caution" or wbgt_category == "High Risk":
            overall_level = "EXTREME CAUTION"
            overall_color = "#e67e22"
            triggers.append(f"Heat Index ({hi:.1f}°C) in Extreme Caution (32°C - 39°C)")
            if wbgt_category == "High Risk":
                triggers.append(f"WBGT ({swbgt:.1f}°C) indicates High Risk for strenuous labor")
            action_recommendations.extend([
                "Fatigue possible with prolonged activity. Limit strenuous exercise.",
                "Ensure regular water consumption and shade access."
            ])
        elif hi_category == "Caution" or wbgt_category == "Moderate Risk":
            overall_level = "CAUTION"
            overall_color = "#f1c40f"
            triggers.append(f"Heat Index ({hi:.1f}°C) in Caution zone (27°C - 32°C)")
            action_recommendations.append("Normal activity acceptable with adequate hydration.")
        else:
            overall_level = "NORMAL"
            overall_color = "#2ecc71"
            triggers.append("Environmental conditions within acceptable thermal comfort envelope.")
            action_recommendations.append("No thermal stress restrictions.")

        return {
            "is_forecast": is_forecast,
            "horizon_hours": horizon_hours,
            "overall_level": overall_level,
            "overall_color": overall_color,
            "thermodynamic_state": {
                "temperature_c": round(temperature_c, 1),
                "relative_humidity_pct": round(relative_humidity_pct, 1),
                "dew_point_c": round(t_dp, 1),
                "wet_bulb_c": round(t_wb, 1),
                "humidity_ratio_g_kg": round(w_ratio, 2),
                "enthalpy_kj_kg": round(enthalpy, 1),
                "heat_index_c": round(hi, 1),
                "swbgt_c": round(swbgt, 1)
            },
            "category_assessments": {
                "imd_heat_wave": imd_eval,
                "noaa_heat_index": {
                    "category": hi_category,
                    "color": hi_color,
                    "value": round(hi, 1)
                },
                "osha_wbgt": {
                    "category": wbgt_category,
                    "color": wbgt_color,
                    "value": round(swbgt, 1)
                }
            },
            "explainability": {
                "primary_triggers": triggers,
                "action_recommendations": action_recommendations,
                "dominant_risk_factor": "Dry Ambient Convection" if (temperature_c >= 40.0 and relative_humidity_pct < 30.0) 
                                        else ("Moisture Evaporation Impedance" if t_wb >= 28.0 else "Normal Balance")
            }
        }

    def generate_multi_horizon_forecast(
        self,
        location_key: str,
        recent_history_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Generates 1h, 3h, 6h, and 24h forecasts and associated early warnings
        from a window of recent historical observations (>= 26 hours required for lags).
        """
        if len(recent_history_df) < 26:
            raise ValueError(f"Need at least 26 hours of continuous history for lag features, got {len(recent_history_df)}")

        # Extract latest observation state
        latest_row = recent_history_df.iloc[-1]
        latest_t = float(latest_row["temperature_c"])
        latest_rh = float(latest_row["relative_humidity_pct"])
        latest_ws = float(latest_row.get("wind_speed_ms", 2.0))
        latest_p = float(latest_row.get("surface_pressure_hpa", STANDARD_PRESSURE_HPA))
        latest_solar = float(latest_row.get("solar_radiation_wm2", 0.0))

        # 1. Current Warning
        current_warning = self.generate_comprehensive_warning(
            temperature_c=latest_t,
            relative_humidity_pct=latest_rh,
            location_key=location_key,
            wind_speed_ms=latest_ws,
            surface_pressure_hpa=latest_p,
            solar_radiation_wm2=latest_solar,
            is_forecast=False,
            horizon_hours=0
        )

        # 2. Multi-Horizon Forecasts
        forecasts = {}
        for h in [1, 3, 6, 24]:
            champ = self._get_champion_model(location_key, h)
            
            # Construct feature vector for time t using recent history (without trimming future rows)
            # Create features on full window and take the last row corresponding to latest observation
            full_feat = create_time_series_features(recent_history_df, horizons=[0]) if len(recent_history_df) > 55 else None
            
            # Generate feature vector directly from recent history
            feat_df = recent_history_df.copy()
            hour = feat_df.index.hour
            month = feat_df.index.month
            feat_df["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
            feat_df["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
            feat_df["month_sin"] = np.sin(2 * np.pi * (month - 1) / 12.0)
            feat_df["month_cos"] = np.cos(2 * np.pi * (month - 1) / 12.0)
            
            for lag in [1, 2, 3, 6, 12, 24]:
                feat_df[f"temp_lag_{lag}"] = feat_df["temperature_c"].shift(lag)
                feat_df[f"rh_lag_{lag}"] = feat_df["relative_humidity_pct"].shift(lag)
                feat_df[f"solar_lag_{lag}"] = feat_df["solar_radiation_wm2"].shift(lag)
                feat_df[f"wind_lag_{lag}"] = feat_df["wind_speed_ms"].shift(lag)
                
            for window in [3, 6, 24]:
                feat_df[f"temp_roll_mean_{window}"] = feat_df["temperature_c"].shift(1).rolling(window).mean()
                feat_df[f"temp_roll_std_{window}"] = feat_df["temperature_c"].shift(1).rolling(window).std()
                feat_df[f"temp_roll_max_{window}"] = feat_df["temperature_c"].shift(1).rolling(window).max()
                feat_df[f"temp_roll_min_{window}"] = feat_df["temperature_c"].shift(1).rolling(window).min()
                feat_df[f"rh_roll_mean_{window}"] = feat_df["relative_humidity_pct"].shift(1).rolling(window).mean()
                
            feat_df["temp_diff_1h"] = feat_df["temperature_c"].shift(1) - feat_df["temperature_c"].shift(2)
            feat_df["temp_diff_24h"] = feat_df["temperature_c"].shift(1) - feat_df["temperature_c"].shift(25)
            feat_df["rh_diff_1h"] = feat_df["relative_humidity_pct"].shift(1) - feat_df["relative_humidity_pct"].shift(2)
            
            latest_feat_row = feat_df[champ["feature_cols"]].iloc[[-1]]
            
            if champ["scaler"] is not None:
                X_scaled = champ["scaler"].transform(latest_feat_row)
                pred_t = float(champ["model_t"].predict(X_scaled)[0])
                pred_rh = float(np.clip(champ["model_rh"].predict(X_scaled)[0], 0.0, 100.0))
            else:
                pred_t = float(champ["model_t"].predict(latest_feat_row)[0])
                pred_rh = float(np.clip(champ["model_rh"].predict(latest_feat_row)[0], 0.0, 100.0))

            # Generate warning evaluation for predicted future state
            h_warning = self.generate_comprehensive_warning(
                temperature_c=pred_t,
                relative_humidity_pct=pred_rh,
                location_key=location_key,
                wind_speed_ms=latest_ws,
                surface_pressure_hpa=latest_p,
                solar_radiation_wm2=0.0,  # Conservatively zero or nocturnal
                is_forecast=True,
                horizon_hours=h
            )
            
            forecasts[f"t_plus_{h}h"] = {
                "horizon_hours": h,
                "model_architecture": champ["model_type"],
                "predicted_temperature_c": round(pred_t, 1),
                "predicted_relative_humidity_pct": round(pred_rh, 1),
                "warning_level": h_warning["overall_level"],
                "warning_color": h_warning["overall_color"],
                "warning_details": h_warning
            }

        return {
            "location": location_key,
            "timestamp_utc": str(recent_history_df.index[-1]),
            "current_status": current_warning,
            "forecasts": forecasts
        }

if __name__ == "__main__":
    engine = AdvancedWarningEngine()
    print("Testing Warning Engine on a severe simulated heat wave condition:")
    res = engine.generate_comprehensive_warning(
        temperature_c=46.2,
        relative_humidity_pct=35.0,
        location_key="new_delhi"
    )
    print("Overall Warning Level:", res["overall_level"])
    print("Primary Triggers:", json.dumps(res["explainability"]["primary_triggers"], indent=2))
    print("Action Recommendations:", json.dumps(res["explainability"]["action_recommendations"], indent=2))
