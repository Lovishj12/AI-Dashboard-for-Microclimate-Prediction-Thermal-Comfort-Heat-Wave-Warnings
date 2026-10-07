# Phase 3 — Scientific Calculation Engine Documentation
**Project**: AI Based Dashboard Development for Microclimate Prediction and Advanced Warning System for Thermal Comfort / Heat Waves  
**Supervisor**: Prof. Chirodeep Bakli  
**Milestone**: Phase 3 Technical Documentation  

---

## 1. Scope & Objective
Phase 3 builds the core physical and biometeorological calculation engine of the system. The engine operates independently of UI and database layers, ensuring modularity, complete testability, and reuse by both the machine learning pipeline (Phases 5–6) and the real-time API server (Phase 8).

---

## 2. Implemented Formulations & Mathematical Derivations

### 2.1 Saturation Vapor Pressure ($e_s$) & Actual Vapor Pressure ($e_a$)
- **Formulation**: Magnus-Tetens equation parameterized by Sonntag (1990) and Buck (1981):
  $$e_s(T) = 6.112 \exp\left(\frac{17.67 \cdot T}{T + 243.5}\right) \quad [\text{hPa}]$$
- **Actual Vapor Pressure**:
  $$e_a = \left(\frac{RH}{100}\right) \cdot e_s(T) \quad [\text{hPa}]$$
- **Valid Range**: $-40^\circ\text{C} \le T \le 50^\circ\text{C}$ (Standard meteorological range).

### 2.2 Dew Point Temperature ($T_{dp}$)
- **Formulation**: Inversion of the Magnus-Tetens relation adopted by the World Meteorological Organization (WMO):
  $$\alpha(T, RH) = \frac{17.67 \cdot T}{T + 243.5} + \ln\left(\frac{RH}{100}\right)$$
  $$T_{dp} = \frac{243.5 \cdot \alpha}{17.67 - \alpha} \quad [^\circ\text{C}]$$
- **Validation**: Strict boundary check confirms $T_{dp} = T_{db}$ when $RH = 100\%$. Accuracy within $\pm 0.1^\circ\text{C}$ over $[0^\circ\text{C}, 50^\circ\text{C}]$.

### 2.3 Wet-Bulb Temperature ($T_{wb}$)
- **Formulation**: Stull (2011) empirical relation based on extensive psychrometric regressions:
  $$T_{wb} = T \cdot \arctan\left(0.151977 \sqrt{RH + 8.313659}\right) + \arctan(T + RH) - \arctan(RH - 1.676331) + 0.00391838 \cdot RH^{1.5} \arctan(0.023101 \cdot RH) - 4.686035 \quad [^\circ\text{C}]$$
- **Source**: Stull, R. (2011). *Journal of Applied Meteorology and Climatology*, 50(11), 2267–2269.
- **Physical Law Verification**: Verified across all conditions that $T_{dp} \le T_{wb} \le T_{db}$.

### 2.4 Humidity Ratio ($W$)
- **Formulation**: Derived from Dalton’s law of partial pressures for moist air (ASHRAE Handbook of Fundamentals):
  $$W = \frac{M_w}{M_{da}} \frac{e_a}{P_{atm} - e_a} = 0.62198 \cdot \frac{e_a}{P_{atm} - e_a} \quad \left[\frac{\text{kg}_w}{\text{kg}_{da}}\right]$$
  where $M_w = 18.015\text{ kg/kmol}$, $M_{da} = 28.966\text{ kg/kmol}$, and $P_{atm}$ is local surface pressure (hPa).

### 2.5 Specific Enthalpy ($h$)
- **Formulation**: ASHRAE thermodynamic energy balance of dry air and associated water vapor:
  $$h = c_{pa} \cdot T + W \cdot (h_{we} + c_{pw} \cdot T) = 1.006 \cdot T + W \cdot (2501.0 + 1.86 \cdot T) \quad \left[\frac{\text{kJ}}{\text{kg}_{da}}\right]$$

### 2.6 NOAA / NWS Heat Index ($HI$)
- **Formulation**: Rothfusz (1990) 9-term polynomial regression with Steadman adjustments for low humidity ($RH < 13\%$, $80^\circ\text{F} \le T \le 112^\circ\text{F}$) and high humidity ($RH > 85\%$, $80^\circ\text{F} \le T \le 87^\circ\text{F}$).
- **Source**: National Weather Service Technical Attachment SR 90-23.

### 2.7 Simplified Wet-Bulb Globe Temperature ($sWBGT$)
- **Formulation**: Australian Bureau of Meteorology (BoM) standard:
  $$\text{sWBGT} = 0.567 \cdot T_{db} + 0.393 \cdot e_a + 3.94 \quad [^\circ\text{C}]$$

---

## 3. Validation Matrix & Benchmark Test Results

The engine was subjected to 8 comprehensive unit tests in [`tests/test_scientific_engine.py`](file:///c:/Users/lovis/Desktop/BTP/tests/test_scientific_engine.py), all passing:

| Benchmark Case | Expected Value | Calculated Value | Error / Discrepancy | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Saturation $e_s(0^\circ\text{C})$** | $6.11\text{ hPa}$ | $6.112\text{ hPa}$ | $< 0.002\text{ hPa}$ | **PASSED** |
| **Saturation State ($30^\circ\text{C}, 100\%\text{ RH}$)** | $T_{dp} = T_{wb} = 30.0^\circ\text{C}$ | $30.0^\circ\text{C}, 30.0^\circ\text{C}$ | $0.0^\circ\text{C}$ | **PASSED** |
| **Stull Wet-Bulb ($20^\circ\text{C}, 50\%\text{ RH}$)** | $13.70^\circ\text{C}$ | $13.68^\circ\text{C}$ | $0.02^\circ\text{C}$ | **PASSED** |
| **Severe Heat Stull ($35^\circ\text{C}, 70\%\text{ RH}$)** | $30.40^\circ\text{C}$ | $30.36^\circ\text{C}$ | $0.04^\circ\text{C}$ | **PASSED** |
| **NOAA HI ($32.22^\circ\text{C} / 90^\circ\text{F}, 70\%\text{ RH}$)**| $41.11^\circ\text{C} / 106.0^\circ\text{F}$ | $41.16^\circ\text{C}$ | $0.05^\circ\text{C}$ | **PASSED** |
| **NOAA Extreme HI ($37.78^\circ\text{C}, 60\%\text{ RH}$)** | $53.89^\circ\text{C} / 129.0^\circ\text{F}$ | $54.10^\circ\text{C}$ | $0.21^\circ\text{C}$ | **PASSED** |
| **ASHRAE Humidity Ratio ($25^\circ\text{C}, 50\%\text{ RH}$)**| $9.87\text{ g/kg}$ | $9.87\text{ g/kg}$ | $< 0.01\text{ g/kg}$ | **PASSED** |
| **ASHRAE Enthalpy ($25^\circ\text{C}, 50\%\text{ RH}$)**| $50.3\text{ kJ/kg}$ | $50.3\text{ kJ/kg}$ | $< 0.01\text{ kJ/kg}$ | **PASSED** |
| **BoM sWBGT ($35^\circ\text{C}, 60\%\text{ RH}$)** | $37.04^\circ\text{C}$ | $37.06^\circ\text{C}$ | $0.02^\circ\text{C}$ | **PASSED** |

---

## 4. Enriched Time-Series Datasets
All 13,128 hourly observations for the three pilot locations were processed through [`src/enrich_datasets.py`](file:///c:/Users/lovis/Desktop/BTP/src/enrich_datasets.py) and output to `data/processed/enriched/`:
- `data/processed/enriched/new_delhi_enriched_hourly.csv`
- `data/processed/enriched/kharagpur_enriched_hourly.csv`
- `data/processed/enriched/ahmedabad_enriched_hourly.csv`

Every record now contains all 8 thermodynamic state variables ready for psychrometric plotting (Phase 4) and ML feature extraction (Phase 5).
