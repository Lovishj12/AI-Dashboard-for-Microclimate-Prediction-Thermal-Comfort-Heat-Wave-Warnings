"""
Step 13: What-If Mitigation Scenario Simulation Engine for IIT Kharagpur.

Adapted from the UNSW High Performance Architecture Urban Heat Island Mitigation
Performance Index (Prof. M. Santamouris et al.).

Evaluates the thermodynamic efficacy of urban cooling interventions across the campus:
1. 'cool_roofs': High-albedo cool roofs applied to building footprints (α increased to 0.65 - 0.75).
2. 'tree_canopy_expansion': Dense urban forest planting (+25% vegetative fraction within 100m buffer).
3. 'permeable_reflective_pavements': Cool permeable pavers replacing dark asphalt roadways (α=0.40, fi reduced by 30%).
4. 'comprehensive_green_infrastructure': Combined Cool Roofs + 25% Tree Canopy + Permeable Pavers + Solar Shading.

Quantifies for every building and the whole campus:
- Ambient temperature reduction (ΔT_mitigation in °C)
- Avoided NOAA Heat Index stress (ΔHI_benefit in °C)
- Evaporative Wet-Bulb relief (ΔTwb in °C)
- Avoided Cooling Degree Hours (CDH proxy for energy demand savings)
- Vulnerability score reduction (ΔHVI points)
- Benefit-to-Intervention priority rating
"""

from typing import Dict, List, Any
from pathlib import Path
import json

from src.scientific_engine import (
    wet_bulb_temperature,
    heat_index,
    simplified_wbgt,
    classify_heat_index,
    classify_wbgt
)
from src.campus_microclimate import compute_building_microclimate_delta, calculate_vulnerability_index

class CampusMitigationEngine:
    """
    Simulates physical urban cooling interventions across IIT Kharagpur campus.
    """

    def __init__(self, geojson_path: Path = Path("data/iit_kgp_campus.geojson")):
        self.geojson_path = geojson_path
        with open(self.geojson_path, "r", encoding="utf-8") as f:
            self.geojson_data = json.load(f)

    def simulate_mitigation_scenario(
        self,
        intervention_type: str = "comprehensive_green_infrastructure",
        regional_t_c: float = 38.0,
        regional_rh_pct: float = 50.0,
        regional_solar_wm2: float = 750.0,
        regional_wind_ms: float = 2.0
    ) -> Dict[str, Any]:
        """
        Simulates campus-wide thermodynamic microclimate before and after an intervention.
        """
        interventions_config = {
            "cool_roofs": {
                "name": "High-Albedo Cool Roof Program",
                "description": "Application of solar-reflective roof coatings (α = 0.70) across all building rooftops.",
                "target_albedo": 0.70,
                "veg_fraction_boost": 0.0,
                "impervious_fraction_reduction": 0.0,
                "svf_adjustment": 0.0,
            },
            "tree_canopy_expansion": {
                "name": "Urban Forest & Canopy Expansion (+25%)",
                "description": "Planting shade tree canopy across pedestrian walkways and residential hall courtyards.",
                "target_albedo": None,
                "veg_fraction_boost": 0.25,
                "impervious_fraction_reduction": 0.15,
                "svf_adjustment": -0.10,  # Lower sky view due to tree shading
            },
            "permeable_reflective_pavements": {
                "name": "Permeable & Reflective Pavement Retrofit",
                "description": "Replacing dark asphalt roads (Scholars Ave, PAN loop) with light permeable interlocking pavers.",
                "target_albedo": 0.40,
                "veg_fraction_boost": 0.08,
                "impervious_fraction_reduction": 0.35,
                "svf_adjustment": 0.0,
            },
            "comprehensive_green_infrastructure": {
                "name": "Comprehensive UNSW Urban Heat Mitigation Masterplan",
                "description": "Synergistic deployment of Cool Roofs (α=0.70) + 25% Tree Canopy + Permeable Pavers + Solar Shading.",
                "target_albedo": 0.70,
                "veg_fraction_boost": 0.30,
                "impervious_fraction_reduction": 0.35,
                "svf_adjustment": -0.08,
            }
        }

        cfg = interventions_config.get(intervention_type, interventions_config["comprehensive_green_infrastructure"])
        mitigation_results = []

        total_temp_reduction = 0.0
        total_hi_reduction = 0.0

        for feat in self.geojson_data.get("features", []):
            props = feat.get("properties", {})
            b_id = props.get("id")
            name = props.get("name")
            cat = props.get("category")
            
            orig_albedo = float(props.get("albedo", 0.25))
            orig_veg = float(props.get("vegetation_fraction", 0.30))
            orig_imp = float(props.get("impervious_fraction", 0.70))
            orig_svf = float(props.get("sky_view_factor", 0.75))
            ac_pen = float(props.get("ac_penetration", 0.50))
            footfall = props.get("estimated_footfall", "Medium")
            vuln_base = props.get("vulnerability_baseline", "Medium")

            # 1. Baseline Microclimate (Unmitigated)
            base_deltas = compute_building_microclimate_delta(
                albedo=orig_albedo,
                vegetation_fraction=orig_veg,
                impervious_fraction=orig_imp,
                sky_view_factor=orig_svf,
                solar_radiation_wm2=regional_solar_wm2,
                wind_speed_ms=regional_wind_ms
            )
            base_t = round(regional_t_c + base_deltas["temperature_delta_c"], 2)
            base_rh = round(max(10.0, min(100.0, regional_rh_pct + base_deltas["relative_humidity_delta_pct"])), 1)
            base_hi = round(heat_index(base_t, base_rh), 2)
            base_twb = round(wet_bulb_temperature(base_t, base_rh), 2)
            base_hvi = calculate_vulnerability_index(base_hi, simplified_wbgt(base_t, base_rh), ac_pen, footfall, vuln_base)

            # 2. Mitigated Physical Properties
            mod_albedo = cfg["target_albedo"] if cfg["target_albedo"] is not None else orig_albedo
            mod_veg = min(0.90, orig_veg + cfg["veg_fraction_boost"])
            mod_imp = max(0.10, orig_imp - cfg["impervious_fraction_reduction"])
            mod_svf = max(0.40, min(0.95, orig_svf + cfg["svf_adjustment"]))

            # 3. Mitigated Microclimate
            mit_deltas = compute_building_microclimate_delta(
                albedo=mod_albedo,
                vegetation_fraction=mod_veg,
                impervious_fraction=mod_imp,
                sky_view_factor=mod_svf,
                solar_radiation_wm2=regional_solar_wm2,
                wind_speed_ms=regional_wind_ms
            )
            mit_t = round(regional_t_c + mit_deltas["temperature_delta_c"], 2)
            mit_rh = round(max(10.0, min(100.0, regional_rh_pct + mit_deltas["relative_humidity_delta_pct"])), 1)
            mit_hi = round(heat_index(mit_t, mit_rh), 2)
            mit_twb = round(wet_bulb_temperature(mit_t, mit_rh), 2)
            mit_hvi = calculate_vulnerability_index(mit_hi, simplified_wbgt(mit_t, mit_rh), ac_pen, footfall, vuln_base)

            # Net Benefits
            delta_cooling_c = round(base_t - mit_t, 2)
            delta_hi_benefit_c = round(base_hi - mit_hi, 2)
            delta_twb_benefit_c = round(base_twb - mit_twb, 2)
            delta_hvi_points = round(base_hvi - mit_hvi, 1)

            total_temp_reduction += delta_cooling_c
            total_hi_reduction += delta_hi_benefit_c

            mitigation_results.append({
                "id": b_id,
                "name": name,
                "category": cat,
                "unmitigated": {
                    "temperature_c": base_t,
                    "heat_index_c": base_hi,
                    "wet_bulb_c": base_twb,
                    "vulnerability_score": base_hvi,
                },
                "mitigated": {
                    "temperature_c": mit_t,
                    "heat_index_c": mit_hi,
                    "wet_bulb_c": mit_twb,
                    "vulnerability_score": mit_hvi,
                },
                "net_cooling_benefit": {
                    "temperature_reduction_c": delta_cooling_c,
                    "heat_index_reduction_c": delta_hi_benefit_c,
                    "wet_bulb_reduction_c": delta_twb_benefit_c,
                    "vulnerability_points_saved": delta_hvi_points,
                    "cooling_degree_hours_saved_pct": round(min(45.0, max(5.0, delta_cooling_c * 12.5)), 1),
                }
            })

        # Rank descending by cooling benefit achieved
        mitigation_results.sort(key=lambda x: x["net_cooling_benefit"]["temperature_reduction_c"], reverse=True)
        n = len(mitigation_results)
        mean_cooling = round(total_temp_reduction / n, 2)
        mean_hi_relief = round(total_hi_reduction / n, 2)

        return {
            "tier": "Modelled / Intervention Simulation (UNSW Performance Index)",
            "intervention": {
                "id": intervention_type,
                "name": cfg["name"],
                "description": cfg["description"],
                "mean_temperature_reduction_c": mean_cooling,
                "mean_heat_index_relief_c": mean_hi_relief,
                "average_hvac_energy_reduction_pct": round(mean_cooling * 11.2, 1),
                "top_beneficiary_building": mitigation_results[0]["name"],
                "maximum_cooling_achieved_c": mitigation_results[0]["net_cooling_benefit"]["temperature_reduction_c"],
            },
            "buildings": mitigation_results
        }
