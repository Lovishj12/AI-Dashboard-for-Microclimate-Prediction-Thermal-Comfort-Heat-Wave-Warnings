# Step 13: What-If Urban Cooling Mitigation Scenarios & Efficacy Engine

## Overview & Academic Background
Step 13 delivers an interactive decision-support engine simulating physical urban microclimate cooling interventions across the 2,100-acre IIT Kharagpur campus. 

The mathematical formulation is directly adapted from the **UNSW High Performance Architecture Urban Heat Island Mitigation Performance Index** led by Prof. M. Santamouris et al. (Sydney, Australia), tailored to IIT Kharagpur's tropical wet-and-dry climate (*Köppen Aw*).

---

## Modeled Interventions

1. **High-Albedo Cool Roof Program (`cool_roofs`)**:
   - Rooftop solar reflectance ($\alpha$) elevated to $0.70$ across building footprints.
   - Mitigates radiative heat absorption in large roof complexes (Nalanda, Main Academic Building, Gymkhana).
2. **Urban Forest & Canopy Expansion (`tree_canopy_expansion`)**:
   - $+25\%$ vegetative fraction buffer added to pedestrian corridors and hall courtyards.
   - Enhances evaporative cooling and reduces sky view factor ($\text{SVF}$) through dense shading canopy.
3. **Permeable & Reflective Pavement Retrofit (`permeable_reflective_pavements`)**:
   - Dark bitumen roads (Scholars Avenue, PAN loop) replaced with high-albedo ($\alpha=0.40$) interlocking permeable pavers.
   - Cuts impervious fraction by $35\%$ and promotes moisture retention.
4. **Comprehensive UNSW Masterplan (`comprehensive_green_infrastructure`)**:
   - Synergistic deployment combining Cool Roofs ($\alpha=0.70$) + $30\%$ Tree Canopy + $35\%$ Impervious Reduction + Shading.

---

## Thermodynamic Quantification Engine (`src/campus_mitigation.py`)

For each campus landmark $i$ and intervention $k$, the engine evaluates:
- $\Delta T_{\text{cooling}, i} = T_{\text{unmitigated}, i} - T_{\text{mitigated}, i} \quad [^\circ\text{C}]$
- $\Delta HI_{\text{relief}, i} = HI(T_{\text{unmitigated}, i}, RH) - HI(T_{\text{mitigated}, i}, RH) \quad [^\circ\text{C}]$
- $\Delta Twb_{\text{relief}, i} = Twb_{\text{unmitigated}, i} - Twb_{\text{mitigated}, i} \quad [^\circ\text{C}]$
- $\Delta HVI_{\text{points}} = HVI_{\text{base}} - HVI_{\text{mitigated}} \quad [\text{points}]$
- $\text{Avoided CDH Proxy (\%)} = \min(45\%, \Delta T_{\text{cooling}} \times 12.5\%)$

---

## API Endpoint Specification

### `GET /api/campus/mitigation`
- **Query Parameter**: `intervention_type` (`cool_roofs`, `tree_canopy_expansion`, `permeable_reflective_pavements`, `comprehensive_green_infrastructure`)
- **Sample Output**:
```json
{
  "tier": "Modelled / Intervention Simulation (UNSW Performance Index)",
  "intervention": {
    "id": "comprehensive_green_infrastructure",
    "name": "Comprehensive UNSW Urban Heat Mitigation Masterplan",
    "description": "Synergistic deployment of Cool Roofs (α=0.70) + 25% Tree Canopy + Permeable Pavers + Solar Shading.",
    "mean_temperature_reduction_c": 1.25,
    "mean_heat_index_relief_c": 2.14,
    "average_hvac_energy_reduction_pct": 14.0,
    "top_beneficiary_building": "Nalanda Classroom Complex",
    "maximum_cooling_achieved_c": 1.95
  },
  "buildings": [...]
}
```

---

## Frontend Integration (`CampusMitigationView.jsx`)
- Interactive 4-tab selector with dedicated color tokens.
- 4 KPI summary cards (Mean Ambient Cooling, Mean Heat Index Relief, HVAC Energy Savings, Top Beneficiary Zone).
- Sticky-header sorted impact table showing baseline vs mitigated temperatures, cooling, and percentage energy saved across all 24 landmarks.

---

## Verification & Testing
- Automated unit test suite: `tests/test_campus_mitigation.py`.
- Tested endpoint response, schema integrity, 4 intervention evaluations, and comprehensive supremacy.
- Result: **PASS** across all assertions.
