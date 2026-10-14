"""
Step 6: Spatial Microclimate Downscaling Engine for IIT Kharagpur.

Scientifically grounded downscaling model adapting the UNSW High Performance Architecture
Urban Heat Island (UHI) empirical framework (Prof. M. Santamouris et al.).

Translates regional synoptic meteorological observations (NASA POWER / IMD Station at Kharagpur)
into building- and precinct-specific microclimatic states based on localized surface physical attributes:
1. Surface Solar Albedo (α): Dark asphalt / concrete absorbing shortwave solar radiation vs cool roofs.
2. Vegetation Fraction (f_v): Tree canopy and green cover providing sensible heat reduction via evapotranspiration.
3. Impervious Fraction (f_i): Paved surface fraction driving thermal mass storage and nocturnal re-radiation.
4. Sky View Factor (SVF): Urban canyon geometry dictating daytime solar radiation capture and nighttime longwave cooling.

Outputs full thermodynamic parameters per building:
- Dry-bulb temperature (T_db) and temperature anomaly (ΔT)
- Relative humidity (RH)
- Stull (2011) Wet-bulb temperature (T_wb)
- NOAA Heat Index (HI)
- Australian BoM Simplified WBGT (sWBGT)
- Heat Vulnerability Score (0-100)
- Thermal Risk Category
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.scientific_engine import (
    wet_bulb_temperature,
    heat_index,
    simplified_wbgt,
    classify_heat_index,
    classify_wbgt,
    humidity_ratio,
    dew_point_temperature
)
from src.campus_ac_inventory import CAMPUS_AC_ENGINE

DATA_PATH = Path("data/iit_kgp_campus.geojson")

def compute_building_microclimate_delta(
    albedo: float,
    vegetation_fraction: float,
    impervious_fraction: float,
    sky_view_factor: float,
    solar_radiation_wm2: float = 500.0,
    wind_speed_ms: float = 2.0,
    anthropogenic_heat_flux_wm2: float = 0.0
) -> Dict[str, float]:
    """
    Computes local microclimate perturbation deltas (ΔT and ΔRH) relative to regional station.
    
    Physical Principles:
    - Albedo perturbation: ΔT_albedo = (0.30 - α) * 2.8 * (solar_rad / 600)
    - Vegetation cooling: ΔT_veg = - (f_v - 0.25) * 2.4 (evapotranspirative flux)
    - Impervious heat storage: ΔT_imp = (f_i - 0.50) * 1.6 (thermal mass inertia)
    - Sky view factor: ΔT_svf = (SVF - 0.70) * 0.9 (solar exposure vs sky radiation exchange)
    - Anthropogenic AC heat rejection: ΔT_anthro = min(0.85, (q_anthro / 150.0) * 0.40)
    - Wind ventilation factor: High wind reduces local microclimatic anomalies.
    """
    # Wind attenuation factor: anomalies diminish with strong convective mixing
    wind_attenuation = 1.0 / (1.0 + 0.15 * max(0.0, wind_speed_ms - 1.0))
    solar_scale = min(1.5, max(0.2, solar_radiation_wm2 / 500.0))

    delta_albedo = (0.30 - albedo) * 2.8 * solar_scale
    delta_veg = - (vegetation_fraction - 0.25) * 2.4
    delta_imp = (impervious_fraction - 0.50) * 1.6
    delta_svf = (sky_view_factor - 0.70) * 0.9 * solar_scale
    # Anthropogenic condenser heat rejection component (empirically bounded to realistic canopy delta)
    delta_anthro = min(0.85, (max(0.0, anthropogenic_heat_flux_wm2) / 150.0) * 0.40)

    raw_temp_delta = (delta_albedo + delta_veg + delta_imp + delta_svf + delta_anthro) * wind_attenuation
    # Clamp perturbation to physically observed urban canopy microclimate bounds [-3.5°C to +4.0°C]
    clamped_temp_delta = max(-3.5, min(4.0, raw_temp_delta))

    # RH perturbation: negative correlation with temperature + positive evapotranspiration from vegetation
    rh_delta = (-1.4 * clamped_temp_delta) + (vegetation_fraction * 3.5)
    
    return {
        "temperature_delta_c": round(clamped_temp_delta, 2),
        "relative_humidity_delta_pct": round(rh_delta, 1),
        "components": {
            "albedo_effect": round(delta_albedo * wind_attenuation, 2),
            "vegetation_effect": round(delta_veg * wind_attenuation, 2),
            "impervious_effect": round(delta_imp * wind_attenuation, 2),
            "svf_effect": round(delta_svf * wind_attenuation, 2),
            "anthropogenic_ac_effect": round(delta_anthro * wind_attenuation, 2),
        }
    }

def calculate_vulnerability_index(
    heat_index_c: float,
    swbgt_c: float,
    ac_penetration: float,
    footfall: str,
    baseline_rating: str
) -> float:
    """
    Computes building-specific Heat Vulnerability Index (HVI) on scale 0 to 100.
    Integrates environmental hazard, built-environment sensitivity, and human exposure.
    """
    footfall_map = {"Low": 10.0, "Medium": 25.0, "High": 45.0, "Very High": 60.0}
    footfall_val = footfall_map.get(footfall, 25.0)

    # 1. Environmental Hazard Component (0 - 40 pts)
    # Scaled from HI threshold: 27°C (0 pts) to 45°C (40 pts)
    hazard_score = min(40.0, max(0.0, (heat_index_c - 27.0) * (40.0 / 18.0)))

    # 2. Sensitivity Component (0 - 35 pts): AC deficit & building type
    # Buildings without central AC expose occupants to outdoor heat penetration
    sensitivity_score = (1.0 - ac_penetration) * 35.0

    # 3. Exposure Component (0 - 25 pts): Footfall density
    exposure_score = (footfall_val / 60.0) * 25.0

    total_hvi = hazard_score + sensitivity_score + exposure_score
    return round(min(100.0, max(0.0, total_hvi)), 1)

class CampusMicroclimateEngine:
    """
    Engine executing campus-wide downscaling for all 24 IIT Kharagpur buildings.
    """

    def __init__(self, geojson_path: Path = DATA_PATH):
        self.geojson_path = geojson_path
        if not self.geojson_path.exists():
            from src.campus_spatial import save_spatial_dataset
            save_spatial_dataset()
        with open(self.geojson_path, "r", encoding="utf-8") as f:
            self.geojson_data = json.load(f)

    def evaluate_all_buildings(
        self,
        regional_temperature_c: float,
        regional_relative_humidity_pct: float,
        regional_wind_speed_ms: float = 2.0,
        regional_solar_radiation_wm2: float = 500.0
    ) -> Dict[str, Any]:
        """
        Computes downscaled microclimates for all 24 buildings across IIT Kharagpur campus.
        Returns detailed building array and summary campus metrics (hottest, coolest, mean UHI delta).
        """
        building_results = []
        features = self.geojson_data.get("features", [])

        for feat in features:
            props = feat.get("properties", {})
            b_id = props.get("id")
            name = props.get("name")
            category = props.get("category")
            
            albedo = float(props.get("albedo", 0.25))
            veg_frac = float(props.get("vegetation_fraction", 0.30))
            imp_frac = float(props.get("impervious_fraction", 0.70))
            svf = float(props.get("sky_view_factor", 0.75))
            ac_pen = float(props.get("ac_penetration", 0.50))
            footfall = props.get("estimated_footfall", "Medium")
            vuln_base = props.get("vulnerability_baseline", "Medium")

            # Retrieve building AC inventory profile and compute active heat rejection
            area_sqm = float(props.get("area_sqm", 5000.0))
            ac_rejection = CAMPUS_AC_ENGINE.calculate_building_heat_rejection(
                building_id=b_id,
                operating_scenario="nominal",
                ambient_temperature_c=regional_temperature_c,
                footprint_area_sqm=area_sqm
            )

            deltas = compute_building_microclimate_delta(
                albedo=albedo,
                vegetation_fraction=veg_frac,
                impervious_fraction=imp_frac,
                sky_view_factor=svf,
                solar_radiation_wm2=regional_solar_radiation_wm2,
                wind_speed_ms=regional_wind_speed_ms,
                anthropogenic_heat_flux_wm2=ac_rejection["anthropogenic_flux_wm2"]
            )

            local_t = round(regional_temperature_c + deltas["temperature_delta_c"], 2)
            local_rh = round(max(10.0, min(100.0, regional_relative_humidity_pct + deltas["relative_humidity_delta_pct"])), 1)
            
            local_twb = round(wet_bulb_temperature(local_t, local_rh), 2)
            local_hi = round(heat_index(local_t, local_rh), 2)
            local_swbgt = round(simplified_wbgt(local_t, local_rh), 2)
            
            hi_class = classify_heat_index(local_hi)
            wbgt_class = classify_wbgt(local_swbgt)

            hvi = calculate_vulnerability_index(
                heat_index_c=local_hi,
                swbgt_c=local_swbgt,
                ac_penetration=ac_pen,
                footfall=footfall,
                baseline_rating=vuln_base
            )

            # Physical Land Surface Temperature (LST / Rooftop Skin Temp) based on surface energy balance
            h_conv = max(8.0, 10.0 + 3.8 * max(0.5, regional_wind_speed_ms))
            net_solar_absorbed = (1.0 - albedo) * regional_solar_radiation_wm2
            surface_delta_t = net_solar_absorbed / h_conv - (veg_frac * 2.5)
            surface_delta_t = surface_delta_t * (0.6 + 0.6 * imp_frac)
            surface_temp_c = round(local_t + max(-1.0, min(14.0, surface_delta_t * 0.45)), 1)

            building_results.append({
                "id": b_id,
                "name": name,
                "category": category,
                "latitude": props.get("latitude"),
                "longitude": props.get("longitude"),
                "physical_attributes": {
                    "albedo": albedo,
                    "vegetation_fraction": veg_frac,
                    "impervious_fraction": imp_frac,
                    "sky_view_factor": svf,
                    "ac_penetration": ac_pen,
                    "estimated_footfall": footfall,
                    "area_sqm": props.get("area_sqm"),
                    "floors": props.get("floors"),
                },
                "ac_inventory": {
                    "evidence_tier": ac_rejection["evidence_tier"],
                    "primary_hvac_type": ac_rejection["primary_hvac_type"],
                    "ac_unit_count_confirmed": ac_rejection["ac_unit_count_confirmed"],
                    "ac_unit_count_estimated": ac_rejection["ac_unit_count_estimated"],
                    "condenser_count_estimated": ac_rejection["condenser_count_estimated"],
                    "cooling_capacity_tons_tr": ac_rejection["cooling_capacity_tons_tr"],
                    "rated_cooling_capacity_kw": ac_rejection["rated_cooling_capacity_kw"],
                    "heat_rejection_kw": ac_rejection["heat_rejection_kw"],
                    "electrical_input_kw": ac_rejection["electrical_input_kw"],
                    "anthropogenic_flux_wm2": ac_rejection["anthropogenic_flux_wm2"],
                    "condenser_placement": ac_rejection["condenser_placement"],
                    "operating_schedule": ac_rejection["operating_schedule"],
                    "source_document": ac_rejection["source_document"],
                    "observation_date": ac_rejection["observation_date"],
                    "microclimatic_canyon_impact": ac_rejection["microclimatic_canyon_impact"]
                },
                "microclimate": {
                    "tier": "Modelled / Estimated (Physics-Downscaled)",
                    "temperature_c": local_t,
                    "surface_temperature_c": surface_temp_c,
                    "temperature_delta_c": deltas["temperature_delta_c"],
                    "relative_humidity_pct": local_rh,
                    "wet_bulb_c": local_twb,
                    "heat_index_c": local_hi,
                    "swbgt_c": local_swbgt,
                    "heat_index_risk": hi_class[0],
                    "risk_color": hi_class[1],
                    "wbgt_risk": wbgt_class[0],
                    "vulnerability_score": hvi,
                },
                "delta_components": deltas["components"]
            })

        # Rank buildings by localized heat index (highest to lowest)
        building_results.sort(key=lambda x: x["microclimate"]["heat_index_c"], reverse=True)

        hottest = building_results[0]
        coolest = building_results[-1]
        mean_delta = round(sum(b["microclimate"]["temperature_delta_c"] for b in building_results) / len(building_results), 2)

        return {
            "tier": "Modelled / Estimated (Physics-Downscaled)",
            "regional_reference": {
                "station": "Kharagpur Regional Station (NASA POWER / IMD)",
                "temperature_c": regional_temperature_c,
                "relative_humidity_pct": regional_relative_humidity_pct,
                "wind_speed_ms": regional_wind_speed_ms,
                "solar_radiation_wm2": regional_solar_radiation_wm2,
            },
            "campus_summary": {
                "total_landmarks": len(building_results),
                "mean_temperature_delta_c": mean_delta,
                "hottest_building": {
                    "id": hottest["id"],
                    "name": hottest["name"],
                    "temperature_c": hottest["microclimate"]["temperature_c"],
                    "heat_index_c": hottest["microclimate"]["heat_index_c"],
                },
                "coolest_building": {
                    "id": coolest["id"],
                    "name": coolest["name"],
                    "temperature_c": coolest["microclimate"]["temperature_c"],
                    "heat_index_c": coolest["microclimate"]["heat_index_c"],
                },
                "thermal_delta_spread_c": round(hottest["microclimate"]["temperature_c"] - coolest["microclimate"]["temperature_c"], 2),
            },
            "buildings": building_results
        }

    def evaluate_heat_wave_scenario(
        self,
        scenario_type: str = "imd_severe_heat_wave",
        base_regional_t_c: float = 38.0,
        base_regional_rh_pct: float = 45.0
    ) -> Dict[str, Any]:
        """
        Simulates campus-scale microclimates under standardized extreme heat wave scenarios:
        1. 'imd_heat_wave': Departure +4.5°C above climatology (plains threshold T_max >= 40°C)
        2. 'imd_severe_heat_wave': Departure +6.5°C above climatology
        3. 'humid_heat_crisis': Elevated dry-bulb (41°C) + monsoonal humidity (65% RH), stress-testing Twb >= 30°C
        4. 'dry_convective_blast': Severe 45°C ambient air with low humidity (22% RH)
        """
        scenarios_config = {
            "imd_heat_wave": {
                "name": "IMD Standard Heat Wave (Departure +4.5°C)",
                "description": "Temperature rises +4.5°C above seasonal climatology with clear skies.",
                "delta_t": 4.5,
                "rh_factor": 0.85,
                "solar_wm2": 880.0,
                "wind_ms": 1.8,
            },
            "imd_severe_heat_wave": {
                "name": "IMD Severe Heat Wave (Departure +6.5°C)",
                "description": "Critical regional heat wave with +6.5°C departure pushing ambient air above 44°C.",
                "delta_t": 6.5,
                "rh_factor": 0.75,
                "solar_wm2": 920.0,
                "wind_ms": 1.5,
            },
            "humid_heat_crisis": {
                "name": "Pre-Monsoon Humid Heat Surge",
                "description": "High temperature coupled with elevated oceanic humidity, testing human wet-bulb survivability.",
                "delta_t": 3.0,
                "rh_factor": 1.45,
                "solar_wm2": 750.0,
                "wind_ms": 2.0,
            },
            "dry_convective_blast": {
                "name": "Dry Northwesterly Convective Blast",
                "description": "Intense desiccating heatwave from central India reaching 45°C with severe desiccating winds.",
                "delta_t": 7.0,
                "rh_factor": 0.50,
                "solar_wm2": 950.0,
                "wind_ms": 3.2,
            }
        }

        cfg = scenarios_config.get(scenario_type, scenarios_config["imd_severe_heat_wave"])
        scenario_t = round(base_regional_t_c + cfg["delta_t"], 2)
        scenario_rh = round(max(10.0, min(95.0, base_regional_rh_pct * cfg["rh_factor"])), 1)

        result = self.evaluate_all_buildings(
            regional_temperature_c=scenario_t,
            regional_relative_humidity_pct=scenario_rh,
            regional_wind_speed_ms=cfg["wind_ms"],
            regional_solar_radiation_wm2=cfg["solar_wm2"]
        )

        # Flag precincts exceeding critical thresholds
        critical_twb_exceeded = [b for b in result["buildings"] if b["microclimate"]["wet_bulb_c"] >= 30.0]
        extreme_hi_exceeded = [b for b in result["buildings"] if b["microclimate"]["heat_index_c"] >= 45.0]

        return {
            "tier": "Modelled / Scenario Simulation (Heat Wave Stress Test)",
            "scenario": {
                "id": scenario_type,
                "name": cfg["name"],
                "description": cfg["description"],
                "regional_temperature_c": scenario_t,
                "regional_relative_humidity_pct": scenario_rh,
                "solar_radiation_wm2": cfg["solar_wm2"],
                "wind_speed_ms": cfg["wind_ms"],
            },
            "stress_test_audit": {
                "critical_twb_count": len(critical_twb_exceeded),
                "critical_twb_landmarks": [b["name"] for b in critical_twb_exceeded],
                "extreme_danger_hi_count": len(extreme_hi_exceeded),
                "extreme_danger_hi_landmarks": [b["name"] for b in extreme_hi_exceeded],
                "institutional_action": (
                    "RED ALERT: Implement emergency cooling centers, cancel outdoor athletics, "
                    "and initiate emergency hydration protocols in non-AC residential halls."
                    if len(extreme_hi_exceeded) > 0 else "ORANGE ALERT: Limit afternoon activities."
                )
            },
            "campus_summary": result["campus_summary"],
            "buildings": result["buildings"]
        }


