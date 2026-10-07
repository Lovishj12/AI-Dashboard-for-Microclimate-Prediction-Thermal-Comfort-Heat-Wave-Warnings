# Step 5: Building Selection & Detail Inspector Panel

**Project Title**: AI Based Dashboard Development for Microclimate Prediction and Advanced Warning System for Thermal Comfort / Heat Waves  
**Phase**: Campus-Scale Upgrade — Step 5 Execution  
**Academic Context**: Bachelor Thesis Project (BTP) — Under the supervision of **Prof. Chirodeep Bakli**  
**Component**: Building-Level Microclimate Inspector & Vulnerability Profile  

---

## 1. Objectives & Scope of Step 5
1. Create a specialized **Building Inspector Component** ([`frontend/src/components/BuildingInspector.jsx`](file:///c:/Users/lovis/Desktop/BTP/frontend/src/components/BuildingInspector.jsx)) providing deep-dive analytics whenever a user clicks any building polygon on the campus map or the quick-navigation bar.
2. Implement backend endpoint `GET /api/campus/building/{building_id}` in [`src/api_server.py`](file:///c:/Users/lovis/Desktop/BTP/src/api_server.py).
3. Compute and present downscaled biometeorological parameters for the specific building:
   - Regional meteorological reference (NASA POWER / IMD station).
   - Local Dry-Bulb Temperature ($T_{db}$) and downscaled $\Delta T$ ($^\circ\text{C}$).
   - Stull (2011) Wet-Bulb Temperature ($T_{wb}$) and NOAA Heat Index ($HI$).
   - Simplified Wet-Bulb Globe Temperature ($\text{sWBGT}$).
   - Built-environment physical attributes (Albedo $\alpha$, Vegetation fraction $f_v$, Impervious fraction $f_i$, SVF, Gross Floor Area, Floors).
   - Vulnerability and human exposure metrics (Footfall density, HVAC/AC Penetration %, Heat Vulnerability Index on 0–100 scale).
   - Clear academic labelling: **Modelled / Estimated (Physics-Downscaled)** to preserve academic integrity.

---

## 2. Implementation Summary

### 2.1 Backend Endpoint (`src/api_server.py`)
- Endpoint: `GET /api/campus/building/{building_id}`.
- Pulls verified spatial features from `data/iit_kgp_campus.geojson`.
- Pulls live/latest regional observations from the Kharagpur time series.
- Applies empirical microclimate perturbation model reflecting surface albedo ($\alpha$), vegetation cooling ($f_v$), impervious thermal mass ($f_i$), and sky view factor ($\text{SVF}$).
- Computes Stull $T_{wb}$, NOAA Heat Index, and BoM $\text{sWBGT}$ using the validated [`src/scientific_engine.py`](file:///c:/Users/lovis/Desktop/BTP/src/scientific_engine.py).
- Synthesizes an interpretable vulnerability index score $[0, 100]$ incorporating footfall and AC deficits.

### 2.2 Frontend UI Component (`frontend/src/components/BuildingInspector.jsx`)
- 3-column glassmorphic analytical layout:
  1. **Downscaled Microclimate**: Local $T_{db}$, $\Delta T$ vs regional station, $RH$, Stull $T_{wb}$, NOAA $HI$, BoM $\text{sWBGT}$.
  2. **Surface & Built-Environment**: Surface Solar Albedo, Vegetation fraction, Impervious fraction, SVF, Footprint area, and floor count.
  3. **Vulnerability & Exposure**: Heat Vulnerability Index score (0–100), Footfall rating, AC penetration %, and baseline risk tag.
- Microclimate Attribution Banner explaining the physical driving mechanisms.

### 2.3 Dashboard Integration (`frontend/src/App.jsx`)
- Seamlessly synced with `selectedBuildingId` from [`CampusMap.jsx`](file:///c:/Users/lovis/Desktop/BTP/frontend/src/components/CampusMap.jsx).
- Closing the inspector or selecting another building dynamically triggers camera fly-to and loads the building profile.

---

## 3. Step 5 Verification & Test Results

```
TEST: Step 5 - Building Detail API Endpoint (Valid Landmark)
Input: GET http://127.0.0.1:8000/api/campus/building/nalanda_complex
Expected: HTTP 200 OK, full physical properties, regional reference, and modelled microclimate metrics
Actual: HTTP 200 OK, returned T_db, T_wb, Heat Index, sWBGT, Vulnerability score (40.0), and attribution rationale
PASS/FAIL: PASS

TEST: Step 5 - Building Detail API Endpoint (Invalid Landmark)
Input: GET http://127.0.0.1:8000/api/campus/building/non_existent_building_xyz
Expected: HTTP 404 Not Found with descriptive error message
Actual: HTTP 404 Not Found ("Building 'non_existent_building_xyz' not found in campus registry")
PASS/FAIL: PASS

TEST: Step 5 - Microclimate Delta Physical Consistency
Input: Compare temperature delta of Tikka Lake Zone vs Scholars Avenue Roadway Corridor
Expected: Delta(Tikka Lake) < Delta(Scholars Avenue) due to vegetative cooling & lower imperviousness
Actual: Delta(Tikka Lake) = -1.2°C vs Delta(Scholars Avenue) = +1.28°C; physical law verified
PASS/FAIL: PASS

TEST: Step 5 - Frontend Production Build
Input: npm run build in frontend/
Expected: Clean compilation with BuildingInspector bundled, exit code 0
Actual: vite build exited with code 0 in 237ms (dist/assets/index-B9Ork0pP.js)
PASS/FAIL: PASS
```

---

## 4. Next Step Ready
- **Step 6**: Implement the **Spatial Microclimate Downscaling Engine** ([`src/campus_microclimate.py`](file:///c:/Users/lovis/Desktop/BTP/src/campus_microclimate.py)), creating a unified campus-wide spatial calculation service that computes all 24 building microclimate states concurrently with full thermodynamic outputs and API endpoint `GET /api/campus/microclimate/current`.
