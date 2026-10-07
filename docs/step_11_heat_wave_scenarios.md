# Step 11: Heat Event / Wave Scenario View

**Project Title**: AI Based Dashboard Development for Microclimate Prediction and Advanced Warning System for Thermal Comfort / Heat Waves  
**Phase**: Campus-Scale Upgrade — Step 11 Execution  
**Academic Context**: Bachelor Thesis Project (BTP) — Under the supervision of **Prof. Chirodeep Bakli**  
**Component**: Heat Wave Stress-Testing Engine (`evaluate_heat_wave_scenario`), REST Endpoint & Interactive UI Panel  

---

## 1. Objectives & Scope of Step 11
1. Simulate extreme synoptic heat wave scenarios across the 2,100-acre IIT Kharagpur campus to stress-test human thermoregulation and institutional infrastructure.
2. Formulate 4 standardized extreme heat wave scenarios:
   - **IMD Standard Heat Wave**: $+4.5^\circ\text{C}$ departure above seasonal climatology with intense insolation ($880\text{ W/m}^2$).
   - **IMD Severe Heat Wave**: Critical $+6.5^\circ\text{C}$ departure pushing regional ambient air above $44^\circ\text{C}$ with severe radiative forcing ($920\text{ W/m}^2$).
   - **Pre-Monsoon Humid Heat Surge**: High temperature coupled with monsoonal oceanic moisture, stress-testing human wet-bulb evaporative tolerance ($T_{wb} \ge 30^\circ\text{C}$).
   - **Dry Convective Blast**: Desiccating northwesterly heat surge reaching $45^\circ\text{C}$ with $950\text{ W/m}^2$ solar load.
3. Expose REST endpoint `GET /api/campus/heatwave` in [`src/api_server.py`](file:///c:/Users/lovis/Desktop/BTP/src/api_server.py).
4. Implement an executive dashboard panel ([`frontend/src/components/HeatWaveScenarioView.jsx`](file:///c:/Users/lovis/Desktop/BTP/frontend/src/components/HeatWaveScenarioView.jsx)) presenting:
   - Critical Wet-Bulb breach counts ($T_{wb} \ge 30^\circ\text{C}$).
   - NOAA Extreme Danger breach counts ($HI \ge 45^\circ\text{C}$).
   - Action directives for campus authorities (emergency hydration centers, outdoor activity moratoriums, hostel cooling protocols).
   - Top-6 most severely impacted hotspots with instant map synchronization.

---

## 2. Implementation Summary

### 2.1 Backend Scenario Engine (`src/campus_microclimate.py`)
- `evaluate_heat_wave_scenario`:
  - Parameterizes forcing temperature, humidity, solar insolation, and wind speeds according to IMD meteorological guidelines.
  - Feeds scenario conditions into `CampusMicroclimateEngine.evaluate_all_buildings`.
  - Audits critical physiological limits ($T_{wb} \ge 30^\circ\text{C}$ and $HI \ge 45^\circ\text{C}$) across all 24 landmarks.
  - Automatically synthesizes institutional action directives (`RED ALERT` vs `ORANGE ALERT`).

### 2.2 Backend Endpoint (`src/api_server.py`)
- Added `GET /api/campus/heatwave`.
- Supports query parameter `scenario_type` (`imd_heat_wave`, `imd_severe_heat_wave`, `humid_heat_crisis`, `dry_convective_blast`).

### 2.3 Frontend Stress-Test UI (`HeatWaveScenarioView.jsx`)
- Interactive tabbed interface to switch between all 4 standardized heat events.
- Executive banner showing scenario forcing temperature, humidity, and solar insolation.
- 3 diagnostic audit cards for Critical Wet-Bulb limits, Extreme Danger Heat Index, and Institutional Emergency Actions.
- Ranked card grid of top-6 impacted hotspots with click-to-focus on map.

---

## 3. Step 11 Verification & Test Results

```
TEST: Step 11 - Heat Wave Scenario Endpoint Defaults & Audit
Input: GET http://127.0.0.1:8000/api/campus/heatwave
Expected: HTTP 200 OK, 24 buildings evaluated, critical Twb and extreme HI counts present
Actual: HTTP 200 OK, returned IMD Severe Heat Wave (+6.5°C departure), 11 buildings exceeding critical Twb >= 30°C
PASS/FAIL: PASS

TEST: Step 11 - Multi-Scenario Parametric Verification
Input: Test all 4 scenarios (imd_heat_wave, imd_severe_heat_wave, humid_heat_crisis, dry_convective_blast)
Expected: All return HTTP 200 with distinct thermodynamic forcing parameters
Actual: All 4 returned HTTP 200 cleanly with valid physical parameters
PASS/FAIL: PASS

TEST: Step 11 - Severe Heat Wave Thermodynamic Amplification
Input: Compare IMD Severe Heat Wave (+6.5°C) vs IMD Standard Heat Wave (+4.5°C)
Expected: T(Severe) > T(Standard), HI(Severe) >= HI(Standard)
Actual: Severe forcing T = 34.82°C vs Standard = 32.82°C; maximum HI amplified accordingly
PASS/FAIL: PASS

TEST: Step 11 - Frontend Production Build
Input: npm run build in frontend/
Expected: Clean compilation with HeatWaveScenarioView component, exit code 0
Actual: vite build exited with code 0 in 296ms (dist/assets/index-DQy3B5JI.js)
PASS/FAIL: PASS
```

---

## 4. Next Step Ready
- **Step 12**: Implement the **Campus Heat Vulnerability Layer** (a specialized GIS vulnerability view incorporating demographic sensitivity, residential non-AC student exposure in PAN loop hostels, elderly campus residents, and athletic facilities).
