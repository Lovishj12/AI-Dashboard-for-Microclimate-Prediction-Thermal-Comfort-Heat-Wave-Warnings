# Step 10: Diurnal Time Animation & Scrubber View

**Project Title**: AI Based Dashboard Development for Microclimate Prediction and Advanced Warning System for Thermal Comfort / Heat Waves  
**Phase**: Campus-Scale Upgrade — Step 10 Execution  
**Academic Context**: Bachelor Thesis Project (BTP) — Under the supervision of **Prof. Chirodeep Bakli**  
**Component**: 24-Hour Diurnal Microclimatic Evolution Engine (`evaluate_diurnal_cycle`), REST Endpoint, & Animated UI Scrubber  

---

## 1. Objectives & Scope of Step 10
1. Simulate the complete **24-Hour Diurnal Microclimatic Cycle** (00:00 to 23:00) across all 24 IIT Kharagpur buildings.
2. Ground the cycle in physical meteorological dynamics:
   - Sinusoidal ambient air temperature curve peaking at $\sim 14:00$ and reaching its minimum pre-dawn at $\sim 05:00$.
   - Inverse relative humidity diurnal curve.
   - Half-wave sinusoidal solar insolation curve reaching $\sim 850\text{ W/m}^2$ at solar noon ($12:00$) and zero at night.
   - Dynamic microclimatic UHI perturbations: daytime albedo solar reflection versus nighttime thermal mass heat retention from high impervious surfaces ($f_i$).
3. Expose REST endpoint `GET /api/campus/diurnal` in [`src/api_server.py`](file:///c:/Users/lovis/Desktop/BTP/src/api_server.py).
4. Integrate a **Diurnal Mode Scrubber & Playback Bar** into [`frontend/src/components/CampusMap.jsx`](file:///c:/Users/lovis/Desktop/BTP/frontend/src/components/CampusMap.jsx):
   - Toggle between *AI Forecasts* and *24h Diurnal Animation*.
   - Play/Pause automated 1-hour/sec animation.
   - Interactive timeline slider ($00:00$ to $23:00$) that smoothly re-shades all building polygons, tooltips, and ranking metrics on the fly.

---

## 2. Implementation Summary

### 2.1 Backend Diurnal Physics Engine (`src/campus_microclimate.py`)
- `evaluate_diurnal_cycle`:
  - Derives sinusoidal solar insolation: $I_{\text{solar}} = \max(0, \sin((h - 6) \pi / 12) \cdot 850)$.
  - Calculates diurnal temperature: $T(h) = T_{\text{mean}} + A_T \cos((h - 14) 2\pi / 24)$.
  - Couples each hour's conditions into `CampusMicroclimateEngine.evaluate_all_buildings`.
  - Produces 24 hourly steps with full building breakdowns and campus summary statistics.

### 2.2 Backend Endpoint (`src/api_server.py`)
- Added `GET /api/campus/diurnal`.
- Extracts Kharagpur's recent 24-hour diurnal temperature and humidity extrema ($T_{\max}, T_{\min}, RH_{\max}, RH_{\min}$) to parameterize the simulation realistically.

### 2.3 Frontend Animation UI (`CampusMap.jsx`)
- Added mode toggle buttons: `[AI Forecasts | 24h Diurnal Animation]`.
- Diurnal controls:
  - `▶ Play 24h` / `⏸ Pause` automated playback ticker.
  - Interactive scrub range input ($0$ to $23$).
  - Current time indicator badge (`00:00` through `23:00`).
- Dynamically recalculates choropleth polygon fills and popups in real-time as the slider moves.

---

## 3. Step 10 Verification & Test Results

```
TEST: Step 10 - Diurnal Simulation Endpoint Structure
Input: GET http://127.0.0.1:8000/api/campus/diurnal
Expected: HTTP 200 OK, exactly 24 hourly frames, 24 buildings per frame, nighttime solar radiation = 0 W/m²
Actual: HTTP 200 OK, 24 frames, hour 00:00 solar = 0 W/m², hour 12:00 solar = 850 W/m²
PASS/FAIL: PASS

TEST: Step 10 - Diurnal Physical Thermodynamics Law Check
Input: Compare regional temperature and solar radiation at hour 14 (peak) vs hour 00 (midnight)
Expected: T(14:00) > T(00:00), campus thermal delta spread > 0°C
Actual: T(14:00) = 33.52°C > T(00:00) = 27.90°C; campus thermal spread = 2.45°C
PASS/FAIL: PASS

TEST: Step 10 - Frontend Production Build
Input: npm run build in frontend/
Expected: Clean compilation with 24h Diurnal Animation controls, exit code 0
Actual: vite build exited with code 0 in 254ms (dist/assets/index-JCk9I9J3.js)
PASS/FAIL: PASS
```

---

## 4. Next Step Ready
- **Step 11**: Implement the **Heat Event / Wave Scenario View** (simulating extreme IMD heat wave condition: $+4.5^\circ\text{C}$ to $+6.5^\circ\text{C}$ departure with dry westerly winds to evaluate campus-wide critical thresholds: $T_{wb} \ge 30^\circ\text{C}$ and $HI \ge 45^\circ\text{C}$).
