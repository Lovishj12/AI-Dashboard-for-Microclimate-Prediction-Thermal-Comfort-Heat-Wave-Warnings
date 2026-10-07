# Step 7: Building-Level Heatmap / Choropleth Map Layer

**Project Title**: AI Based Dashboard Development for Microclimate Prediction and Advanced Warning System for Thermal Comfort / Heat Waves  
**Phase**: Campus-Scale Upgrade — Step 7 Execution  
**Academic Context**: Bachelor Thesis Project (BTP) — Under the supervision of **Prof. Chirodeep Bakli**  
**Component**: Interactive Thematic Heatmap Choropleth Layer & Dynamic Legend UI  

---

## 1. Objectives & Scope of Step 7
1. Enhance the interactive campus map ([`frontend/src/components/CampusMap.jsx`](file:///c:/Users/lovis/Desktop/BTP/frontend/src/components/CampusMap.jsx)) to support multi-layer choropleth visualizations.
2. Provide a layer mode selector allowing real-time switching between 5 thematic layers:
   - **NOAA Heat Index ($^\circ\text{C}$)**: Apparent temperature & thermal stress tiers (Safe, Caution, Extreme Caution, Danger).
   - **Stull Wet-Bulb ($^\circ\text{C}$)**: Evaporative cooling limits & physiological threshold approaching $30^\circ\text{C}$.
   - **Urban Heat Island Perturbation ($\Delta T$)**: Local temperature anomaly relative to the Kharagpur regional station (Cooling islands vs severe hotspots).
   - **Heat Vulnerability Index (HVI, 0–100)**: Multi-factorial vulnerability incorporating environmental hazard, non-AC sensitivity, and footfall density.
   - **Landmark Category**: Traditional zoning classification (Academic, Hostel, Sports, Water Body, Corridors).
3. Connect the frontend directly with the unified downscaling endpoint (`GET /api/campus/microclimate/current`).
4. Display a dynamic legend corresponding to the active thematic view with clear scale stops and color indicators.
5. Upgrade tooltip and popup contents to show the active metric and full thermodynamic breakdown for each selected polygon.

---

## 2. Implementation Summary

### 2.1 Thematic Layer Color Ramps (`CampusMap.jsx`)
- **NOAA Heat Index**:
  - $< 27^\circ\text{C}$: Emerald Safe (`#10b981`)
  - $27 - 32^\circ\text{C}$: Blue Caution (`#3b82f6`)
  - $32 - 39^\circ\text{C}$: Amber Extreme Caution (`#f59e0b`)
  - $39 - 45^\circ\text{C}$: Red Danger (`#ef4444`)
  - $\ge 45^\circ\text{C}$: Maroon Extreme Danger (`#881337`)
- **Stull Wet-Bulb**:
  - $< 26^\circ\text{C}$: Green Optimal (`#10b981`)
  - $26 - 28^\circ\text{C}$: Cyan Moderate (`#06b6d4`)
  - $28 - 30^\circ\text{C}$: Amber Elevated (`#f59e0b`)
  - $\ge 30^\circ\text{C}$: Red Critical Human Tolerance (`#ef4444`)
- **Microclimate Delta $\Delta T$**:
  - $\le -1.0^\circ\text{C}$: Cyan Strong Cooling Island (`#06b6d4`)
  - $-1.0 \text{ to } 0.0^\circ\text{C}$: Emerald Mild Cooling Island (`#10b981`)
  - $0.0 \text{ to } +0.8^\circ\text{C}$: Amber Moderate UHI (`#f59e0b`)
  - $> +0.8^\circ\text{C}$: Red Severe Hotspot (`#ef4444`)
- **Heat Vulnerability Index (HVI)**:
  - $< 40$: Low (`#10b981`)
  - $40 - 60$: Moderate (`#f59e0b`)
  - $60 - 75$: High (`#f97316`)
  - $> 75$: Extreme (`#ef4444`)

### 2.2 Integration & SEO Update
- Updated [`frontend/index.html`](file:///c:/Users/lovis/Desktop/BTP/frontend/index.html) with descriptive academic metadata and document title: *"IIT Kharagpur Microclimate & Heat-Risk Intelligence System"*.
- Built production bundle with zero warnings or errors (`dist/assets/index-CmlLx_Or.js`, `245ms`).

---

## 3. Step 7 Verification & Test Results

```
TEST: Step 7 - Downscaled Microclimate Feed for Heatmap Polygons
Input: GET http://127.0.0.1:8000/api/campus/microclimate/current
Expected: HTTP 200 OK with 24 evaluated buildings and valid thermal delta spread
Actual: Returned 24 buildings; Hottest: Central Industrial Workshop Complex; Coolest: Tikka Lake & Wetland Zone
PASS/FAIL: PASS

TEST: Step 7 - Frontend Layer Switching & Production Build
Input: npm run build in frontend/
Expected: Clean compilation with multi-layer choropleth logic bundled, exit code 0
Actual: vite build exited with code 0 in 245ms (dist/assets/index-CmlLx_Or.js generated)
PASS/FAIL: PASS

TEST: Step 7 - Dynamic Thematic Coloring Law Check
Input: Evaluate color stops for Tikka Lake (Delta = -1.05°C) vs Central Workshop (Delta = +1.15°C)
Expected: Tikka Lake renders cool color (#06b6d4), Central Workshop renders hotspot color (#ef4444)
Actual: Color stops map cleanly according to defined intervals
PASS/FAIL: PASS
```

---

## 4. Next Step Ready
- **Step 8**: Implement **Spatial ML Forecasting at Building Scale** ([`src/campus_forecast.py`](file:///c:/Users/lovis/Desktop/BTP/src/campus_forecast.py)), coupling the location-trained champion AI model forecasts ($t+1\text{h}, t+3\text{h}, t+6\text{h}, t+24\text{h}$) with building-level physical downscaling and exposing `GET /api/campus/forecast/{horizon_hours}`.
