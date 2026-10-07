# Step 8: Spatial ML Forecasting Engine at Building Scale

**Project Title**: AI Based Dashboard Development for Microclimate Prediction and Advanced Warning System for Thermal Comfort / Heat Waves  
**Phase**: Campus-Scale Upgrade — Step 8 Execution  
**Academic Context**: Bachelor Thesis Project (BTP) — Under the supervision of **Prof. Chirodeep Bakli**  
**Component**: Building-Scale Spatial ML Forecast Module (`src/campus_forecast.py`), API & UI Timeline  

---

## 1. Objectives & Scope of Step 8
1. Bridge the location-trained regional champion AI forecasting models (Phases 5–6) with the spatial downscaling engine (Step 6) to produce building-level multi-horizon microclimate forecasts:
   - **$t+1\text{h}$**: Immediate tactical warning and short-term dispatch.
   - **$t+3\text{h}$**: Midday transition / class passing heat advisory.
   - **$t+6\text{h}$**: Peak afternoon exposure & outdoor sports restriction.
   - **$t+24\text{h}$**: Next-day operational planning & hostel advisory.
2. Implement `CampusSpatialForecastEngine` in [`src/campus_forecast.py`](file:///c:/Users/lovis/Desktop/BTP/src/campus_forecast.py).
3. Expose REST endpoints:
   - `GET /api/campus/forecast` (all 4 horizons for all 24 buildings).
   - `GET /api/campus/forecast/{horizon_hours}` (single horizon).
4. Integrate a **Timeline Selector** (`Now`, `+1h`, `+3h`, `+6h`, `+24h`) into [`frontend/src/components/CampusMap.jsx`](file:///c:/Users/lovis/Desktop/BTP/frontend/src/components/CampusMap.jsx) enabling live choropleth map updates based on AI predictions.

---

## 2. Implementation Summary

### 2.1 Backend Forecasting Engine (`src/campus_forecast.py` & `src/api_server.py`)
- Evaluates recent 60-hour Kharagpur meteorological telemetry through `WARNING_ENGINE.generate_multi_horizon_forecast`.
- Feeds predicted temperatures ($T_{db}$) and humidities ($RH$) into `CAMPUS_MICROCLIMATE_ENGINE.evaluate_all_buildings`.
- Computes downscaled Stull $T_{wb}$, NOAA $HI$, BoM $\text{sWBGT}$, and Heat Vulnerability Index (HVI) across all 24 landmarks for each forecast horizon.
- Validates inputs strictly (`400 Bad Request` for invalid horizons).

### 2.2 Frontend Map UI Timeline Controls (`CampusMap.jsx`)
- Added a segmented **Timeline Selector** in the map header bar: `[Now, +1h, +3h, +6h, +24h]`.
- Switching timeline dynamically fetches downscaled AI forecasts and immediately updates polygon fill colors and popup metrics across the campus map.

---

## 3. Step 8 Verification & Test Results

```
TEST: Step 8 - Multi-Horizon Spatial Forecast Endpoint
Input: GET http://127.0.0.1:8000/api/campus/forecast
Expected: HTTP 200 OK, complete multi-horizon dictionary with horizons [1, 3, 6, 24] and 24 buildings per horizon
Actual: HTTP 200 OK, full payload generated with HistGradientBoosting and Ridge models
PASS/FAIL: PASS

TEST: Step 8 - Single-Horizon Spatial Forecast Endpoint
Input: GET http://127.0.0.1:8000/api/campus/forecast/6
Expected: HTTP 200 OK, exactly 24 buildings with predicted T_db, HI, Twb, and HVI
Actual: HTTP 200 OK, horizon_label="t+6h", 24 buildings evaluated
PASS/FAIL: PASS

TEST: Step 8 - Invalid Horizon Boundary Handling
Input: GET http://127.0.0.1:8000/api/campus/forecast/12
Expected: HTTP 400 Bad Request with descriptive message
Actual: HTTP 400 Bad Request ("Horizon 12h invalid. Choose from 1, 3, 6, or 24.")
PASS/FAIL: PASS

TEST: Step 8 - Frontend Production Build
Input: npm run build in frontend/
Expected: Clean compilation with Timeline Selector, exit code 0
Actual: vite build exited with code 0 in 229ms (dist/assets/index-D9HhDqmb.js)
PASS/FAIL: PASS
```

---

## 4. Next Step Ready
- **Step 9**: Implement the **Campus Vulnerability & Risk Ranking View** (a dedicated ranking table / drawer sorting all 24 campus buildings by Heat Index, $\Delta T$ severity, and Heat Vulnerability Index score with direct click-to-focus on the map).
