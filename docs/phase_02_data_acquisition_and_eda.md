# Phase 2 — Data Acquisition & Exploratory Data Analysis (EDA) Report
**Project**: AI Based Dashboard Development for Microclimate Prediction and Advanced Warning System for Thermal Comfort / Heat Waves  
**Supervisor**: Prof. Chirodeep Bakli  
**Milestone**: Phase 2 Documentation  

---

## 1. Data Pipeline Overview & Architecture

In accordance with the Phase 1 scientific specification, we implemented an automated, reproducible data ingestion and auditing pipeline:
- **Primary Source**: NASA POWER (Prediction Of Worldwide Energy Resources) Hourly Surface Meteorological API (`SB` Sustainable Buildings Community).
- **Temporal Horizon**: 18 consecutive months (2023-01-01 00:00 UTC to 2024-06-30 23:00 UTC), capturing complete annual cycles and two consecutive severe pre-monsoon heat wave seasons (April–June 2023 and 2024).
- **Pilot Geographic Benchmarks**:
  1. **New Delhi (Safdarjung)**: $28.6139^\circ\text{N}, 77.2090^\circ\text{E}$ (Composite / semi-arid climate characterized by extreme dry heat waves, record summer maximums $\sim 48.5^\circ\text{C}$).
  2. **Kharagpur (IIT Campus / WB)**: $22.3149^\circ\text{N}, 87.3105^\circ\text{E}$ (Tropical wet-and-dry climate characterized by high humidity accompanied by elevated temperatures, producing severe physiological heat stress and high wet-bulb temperatures).
  3. **Ahmedabad**: $23.0225^\circ\text{N}, 72.5714^\circ\text{E}$ (Hot semi-arid climate prone to sustained heat waves and municipal Heat Action Plan implementation).

---

## 2. Ingested Variables & Physical Units

| Parameter Code | Clean Scientific Variable Name | Unit | Physical Measurement / Description |
| :--- | :--- | :--- | :--- |
| `T2M` | `temperature_c` | $^\circ\text{C}$ | Dry-bulb ambient air temperature at $2\text{ m}$ above ground |
| `RH2M` | `relative_humidity_pct` | $\%$ | Relative humidity at $2\text{ m}$ above ground |
| `WS2M` | `wind_speed_ms` | $\text{m/s}$ | Wind speed at $2\text{ m}$ height |
| `PS` | `surface_pressure_hpa` | $\text{hPa}$ | Atmospheric surface pressure (converted from $\text{kPa}$) |
| `ALLSKY_SFC_SW_DWN`| `solar_radiation_wm2` | $\text{W/m}^2$ | All-sky shortwave surface downward solar irradiance |

---

## 3. Data Integrity & Completeness Audit

The ingested datasets were evaluated across temporal monotonicity, missing value detection, duplicates, and range validity:

| Metric | New Delhi | Kharagpur | Ahmedabad | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Total Ingested Records** | 13,128 | 13,128 | 13,128 | **Verified (100%)** |
| **Expected Hourly Records** | 13,128 | 13,128 | 13,128 | **Verified** |
| **Missing Timestamps** | 0 | 0 | 0 | **Zero Gap** |
| **Duplicate Timestamps** | 0 | 0 | 0 | **Monotonic Index** |
| **Missing / Null Values** | 0 across all cols | 0 across all cols | 0 across all cols | **Zero Nulls** |
| **Minimum Temperature** | $0.45^\circ\text{C}$ (Jan winter) | $6.45^\circ\text{C}$ | $6.72^\circ\text{C}$ | **Plausible** |
| **Maximum Temperature** | $48.50^\circ\text{C}$ (May 2024 heat wave)| $46.75^\circ\text{C}$ | $47.44^\circ\text{C}$ | **Plausible** |
| **Hours $\ge 40^\circ\text{C}$ (Plains Base)** | 685 hours | 400 hours | 730 hours | **Statistically Significant Heat** |
| **Hours $\ge 45^\circ\text{C}$ (IMD Heat Wave)**| 166 hours | 13 hours | 60 hours | **Severe Heat Regime** |

---

## 4. Key Scientific & Exploratory Insights

1. **Dry Heat vs. Humid Heat Contrast**:
   - **New Delhi & Ahmedabad** exhibit extreme peak dry-bulb temperatures ($48.5^\circ\text{C}$ and $47.4^\circ\text{C}$) accompanied by low daytime relative humidity ($10\% - 25\%$). This regime aligns with classic convective heat-wave conditions.
   - **Kharagpur** shows moderate peak dry-bulb temperatures ($46.7^\circ\text{C}$), but sustains significantly higher daytime relative humidity ($50\% - 85\%$), producing very high humidity ratios ($W$) and elevated wet-bulb temperatures ($T_{wb}$). In Kharagpur, thermal stress is dominated by evaporative cooling impedance rather than dry air temperature alone.
2. **Diurnal Cycle Consistency**:
   - Surface temperatures exhibit strong sinusoidal daily profiles peaking between 14:00 and 16:00 local solar time, lagging peak solar irradiance ($12:00-13:00$) by $2-3$ hours due to surface thermal inertia.
3. **Heat Wave Frequency in 2024**:
   - The May–June 2024 heat wave was intensely manifested in the Delhi dataset with 166 hours exceeding $45^\circ\text{C}$, providing an ideal real-world ground truth benchmark for our ML forecasting and early-warning algorithms in subsequent phases.

---

## 5. Artifacts and Diagnostic Plots
- Summary plots saved:
  - `reports/eda/new_delhi_eda_overview.png`
  - `reports/eda/kharagpur_eda_overview.png`
  - `reports/eda/ahmedabad_eda_overview.png`
- Audit reports:
  - `reports/eda/new_delhi_eda_report.json`
  - `reports/eda/kharagpur_eda_report.json`
  - `reports/eda/ahmedabad_eda_report.json`
  - `reports/eda/eda_cross_location_summary.csv`
- Unit test suite: `tests/test_data_pipeline.py` (all tests passing).
