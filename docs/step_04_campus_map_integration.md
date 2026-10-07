# Step 4: Interactive Campus Map Integration

**Project Title**: AI Based Dashboard Development for Microclimate Prediction and Advanced Warning System for Thermal Comfort / Heat Waves  
**Phase**: Campus-Scale Upgrade — Step 4 Execution  
**Academic Context**: Bachelor Thesis Project (BTP) — Under the supervision of **Prof. Chirodeep Bakli**  
**Component**: Interactive Leaflet Campus Map UI & Backend GeoJSON Integration  

---

## 1. Objectives & Scope of Step 4
1. Integrate an interactive map viewer (`react-leaflet` + `leaflet`) into the React frontend.
2. Serve the verified 24-landmark IIT Kharagpur campus spatial dataset (`data/iit_kgp_campus.geojson`) via the FastAPI backend (`GET /api/campus/buildings`).
3. Display all campus zones as colored vector polygons categorized by functional typology:
   - **Academic**: Blue (`#3b82f6`)
   - **Hostel (Hall of Residence)**: Purple (`#8b5cf6`)
   - **Sports & Recreation**: Emerald (`#10b981`)
   - **Water Body & Wetlands**: Cyan (`#06b6d4`)
   - **Commercial / Amenities / Health**: Amber (`#f59e0b`)
4. Enable interactive tooltips and popups displaying real physical microclimate parameters:
   - Surface Albedo ($\alpha$)
   - Vegetation Fraction ($f_v$)
   - Impervious Fraction ($f_i$)
   - Sky View Factor (SVF)
   - Baseline Vulnerability Rating
5. Provide a "Quick Navigate" bar for fast camera fly-to transitions across core landmarks (Main Building, Nalanda, Takshashila, Nehru Museum, Tikka Lake, PAN loop hostels).

---

## 2. Implementation Summary

### 2.1 Backend Endpoint (`src/api_server.py`)
- Endpoint: `GET /api/campus/buildings`
- Reads `data/iit_kgp_campus.geojson` and returns the FeatureCollection with HTTP 200 and standard CORS headers.
- Tested with PowerShell `Invoke-RestMethod` returning all 24 features cleanly.

### 2.2 Frontend Component (`frontend/src/components/CampusMap.jsx`)
- Built using `react-leaflet` (`MapContainer`, `TileLayer`, `Polygon`, `Popup`, `Tooltip`, `useMap`).
- High-contrast CARTO Dark Matter basemap tiles: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`.
- Dynamic polygon styling with category-based fills, hover tooltips, and popups with action buttons.
- Camera controller (`CampusViewportHandler`) with smooth `flyToBounds` transitions when a building is selected.
- Quick navigation buttons for one-click selection of major campus centers.

### 2.3 Dashboard Integration (`frontend/src/App.jsx` & `frontend/src/index.css`)
- Imported Leaflet stylesheet `leaflet/dist/leaflet.css` in `index.css`.
- Mounted `<CampusMap selectedBuildingId={selectedBuildingId} onSelectBuilding={setSelectedBuildingId} />` right above the scientific visualizers.
- Successfully built via Vite: `✓ 60 modules transformed`, bundle output generated in `243ms` with zero syntax or bundling errors.

---

## 3. Step 4 Verification & Test Results

```
TEST: Step 4 - Backend Campus GeoJSON API Endpoint
Input: GET http://127.0.0.1:8000/api/campus/buildings
Expected: HTTP 200 OK, FeatureCollection containing 24 Polygon features
Actual: HTTP 200 OK, exactly 24 polygon features returned with complete property schemas
PASS/FAIL: PASS

TEST: Step 4 - Frontend Production Bundle & Compilation
Input: npm run build in frontend directory
Expected: Successful Vite compilation with Leaflet assets bundled, exit code 0
Actual: vite build exited with code 0 in 243ms (dist/assets/index-CjneGPvM.js generated)
PASS/FAIL: PASS

TEST: Step 4 - Frontend Dev Server Health & Integration
Input: HTTP GET http://127.0.0.1:5173/
Expected: HTTP 200 OK with Leaflet script and component mounted
Actual: HTTP 200 OK response from Vite dev server
PASS/FAIL: PASS
```

---

## 4. Next Step Ready
- **Step 5**: Implement the **Building Selection & Detail Inspector Panel** (showing building-specific heat risk profile, local physical parameters, estimated microclimate delta, and vulnerability metrics upon polygon click).
