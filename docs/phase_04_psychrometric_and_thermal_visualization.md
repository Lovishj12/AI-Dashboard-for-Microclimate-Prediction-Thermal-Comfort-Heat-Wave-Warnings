# Phase 4 — Psychrometric & Thermal Comfort Visualization Report
**Project**: AI Based Dashboard Development for Microclimate Prediction and Advanced Warning System for Thermal Comfort / Heat Waves  
**Supervisor**: Prof. Chirodeep Bakli  
**Milestone**: Phase 4 Technical Documentation  

---

## 1. Scope & Thermodynamic Visualization Principles

A central objective emphasized by the project supervisor was to construct a **mathematically rigorous, scientifically grounded psychrometric representation**, rather than an arbitrary decorative chart.

In Phase 4, we built [`src/visualization_engine.py`](file:///c:/Users/lovis/Desktop/BTP/src/visualization_engine.py), which plots thermodynamic states directly in the classic Carrier/ASHRAE coordinate system at standard atmospheric pressure ($P_{atm} = 1013.25\text{ hPa}$):
- **Abscissa (X-Axis)**: Dry-bulb ambient air temperature ($T_{db}$) in $^\circ\text{C}$ ($0^\circ\text{C}$ to $52^\circ\text{C}$).
- **Ordinate (Y-Axis)**: Humidity ratio ($W$) in $\text{g}$ water vapor per $\text{kg}$ dry air ($0$ to $35\text{ g/kg}$).

---

## 2. Implemented Visual Components

### 2.1 The Mathematical Psychrometric Grid
1. **Saturation Curve ($100\%\text{ RH}$)**:
   - Generated dynamically from the Magnus-Tetens vapor pressure equation:
     $$e_s(T) = 6.112 \exp\left(\frac{17.67 T}{T + 243.5}\right)$$
     $$W_{sat}(T) = 0.62198 \cdot \frac{e_s(T)}{P_{atm} - e_s(T)} \cdot 1000 \quad [\text{g/kg}]$$
   - Forms the upper physical envelope boundary where $T_{db} = T_{wb} = T_{dp}$.
2. **Relative Humidity ($RH\%$) Isopleths**:
   - Calculated for $10\%, 20\%, 30\%, \dots, 90\%$ curves intersecting across the domain.
3. **Wet-Bulb Temperature ($T_{wb}$) Diagonals**:
   - Plotted along lines of constant thermodynamic wet-bulb saturation:
     $$W = W_{sat}(T_{wb}) - \frac{c_{pa}}{h_{fg}} (T_{db} - T_{wb})$$
   - Showing labeled diagonals for $10^\circ\text{C}, 15^\circ\text{C}, 20^\circ\text{C}, 25^\circ\text{C}, 30^\circ\text{C}, 35^\circ\text{C}$ wet-bulb temperatures.
4. **ASHRAE Standard 55 Summer Thermal Comfort Polygon**:
   - Projected onto the psychrometric chart for sedentary individuals in typical summer clothing ($0.5\text{ clo}$, $1.1\text{ met}$):
     - Operative/dry-bulb range: $23.5^\circ\text{C} - 28.5^\circ\text{C}$
     - Upper humidity ratio boundary: $W \le 12.0\text{ g/kg}$ (dew point $\sim 16.8^\circ\text{C}$)
     - Lower humidity ratio boundary: $W \ge 4.5\text{ g/kg}$
5. **Observed Microclimate Scatter & Extreme Heat Wave Trajectories**:
   - Displays real annual microclimate observations colored by NOAA Heat Index ($HI$).
   - Highlights the 48-hour diurnal trajectory during the record-setting heat wave of late May 2024 with peak markers.

### 2.2 Thermal Stress Phase-Space Diagram
- Two-dimensional contour plot of **Dry-Bulb Temperature ($T_{db}$) vs. Relative Humidity ($RH\%$)**.
- Displays the continuous NOAA Heat Index gradient partitioned into official NWS risk bands:
  - **Normal** ($HI < 27^\circ\text{C}$) — Light Green
  - **Caution** ($27^\circ\text{C} \le HI < 32^\circ\text{C}$) — Light Yellow
  - **Extreme Caution** ($32^\circ\text{C} \le HI < 39^\circ\text{C}$) — Light Orange
  - **Danger** ($39^\circ\text{C} \le HI < 51^\circ\text{C}$) — Light Red
  - **Extreme Danger** ($HI \ge 51^\circ\text{C}$) — Purple
- Overlays real observations colored by Wet-Bulb Temperature ($T_{wb}$), vividly demonstrating how high humidity dramatically amplifies thermal stress even at sub-$40^\circ\text{C}$ temperatures.

### 2.3 Diurnal Multi-Parameter Heat Wave Dynamics
- Synchronized multi-trace temporal profiles during extreme heat wave weeks:
  - Panel 1: Concurrent traces of Dry-Bulb ($T_{db}$), NOAA Heat Index, Simplified WBGT ($\text{sWBGT}$), Wet-Bulb ($T_{wb}$), and Dew Point ($T_{dp}$) relative to IMD $45^\circ\text{C}$ severe heat thresholds.
  - Panel 2: Inverted diurnal relationship between Relative Humidity and downward solar irradiance ($W/m^2$).

---

## 3. Comparative Observations Between Pilot Stations

| Location | Psychrometric State Distribution | Dominant Heat Stress Mechanism |
| :--- | :--- | :--- |
| **New Delhi** | Extreme rightward elongation along the dry-bulb axis ($T_{db}$ reaching $48.5^\circ\text{C}$), with low moisture ratio ($W \approx 5-12\text{ g/kg}$) during summer heat waves. | **Extreme Convective / Radiative Heat Wave**: Dry air allows sweat evaporation, but ambient air temperature exceeds human core temperature by $>11^\circ\text{C}$, causing severe sensible heat gain. |
| **Kharagpur** | Distinct upward-right cluster with high humidity ratios ($W$ reaching $22-26\text{ g/kg}$) and high wet-bulb temperatures ($T_{wb}$ exceeding $29^\circ\text{C}$). | **Moisture-Saturated Heat Stress**: Sweat cannot effectively evaporate from the skin surface; dangerous heat strain occurs even when $T_{db}$ is under $40^\circ\text{C}$. |
| **Ahmedabad** | Broad distribution across $T_{db} = 25^\circ\text{C} - 47.4^\circ\text{C}$ with summer moisture ratios $W \approx 8-16\text{ g/kg}$. | **Sustained Heat Wave**: Prolonged hours above $40^\circ\text{C}$ with severe midday Heat Index values ($>45^\circ\text{C}$). |

---

## 4. Generated Visualization Artifacts
The following publication-quality visualization assets were rendered into [`reports/visualizations/`](file:///c:/Users/lovis/Desktop/BTP/reports/visualizations):
- **New Delhi**:
  - `new_delhi_psychrometric_chart.png`
  - `new_delhi_thermal_stress_phase_space.png`
  - `new_delhi_diurnal_heat_wave_dynamics.png`
- **Kharagpur**:
  - `kharagpur_psychrometric_chart.png`
  - `kharagpur_thermal_stress_phase_space.png`
  - `kharagpur_diurnal_heat_wave_dynamics.png`
- **Ahmedabad**:
  - `ahmedabad_psychrometric_chart.png`
  - `ahmedabad_thermal_stress_phase_space.png`
  - `ahmedabad_diurnal_heat_wave_dynamics.png`
