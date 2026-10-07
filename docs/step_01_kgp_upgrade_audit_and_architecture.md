# Step 1: Existing Project Audit & UNSW-Inspired System Architecture

**Project Title**: AI Based Dashboard Development for Microclimate Prediction and Advanced Warning System for Thermal Comfort / Heat Waves  
**Upgrade Scope**: Campus-Scale Microclimate Mapping & Heat-Risk Decision-Support System for IIT Kharagpur  
**Academic Context**: Bachelor Thesis Project (BTP) — Under the supervision of **Prof. Chirodeep Bakli**  
**Primary Conceptual Reference**: UNSW High Performance Architecture (Prof. M. Santamouris et al.) & UHI Mitigation Performance Index  

---

## 1. CURRENT SYSTEM AUDIT (What Phases 1–9 Provide)

We inspected the complete existing codebase and evaluated its capabilities:

### 1.1 What Already Works (Solid Assets to Retain 100%)
1. **Scientific Calculation Engine (`src/scientific_engine.py`)**:
   - Rigorously validated implementations of Saturation & Vapor Pressure ($e_s, e_a$), Magnus Dew Point ($T_{dp}$), Stull (2011) Wet-Bulb ($T_{wb}$), ASHRAE Humidity Ratio ($W$) and Enthalpy ($h$), NOAA/NWS Rothfusz Heat Index ($HI$), and Australian BoM Simplified WBGT ($\text{sWBGT}$).
   - Boundary tested and benchmarked against official NOAA tables and psychrometric standards (all 8 unit tests passing).
2. **Data Pipeline & Climatology (`src/data_ingestion.py`, `src/config.py`)**:
   - Continuous 18-month hourly meteorological time series ($13,128$ records per location) already includes Kharagpur (`22.3149° N, 87.3105° E`).
   - Normal climatological maximum temperatures, IMD criteria, and warning parameters are already configured.
3. **AI/ML Multi-Horizon Forecasting Engine (`src/baseline_model.py`, `src/advanced_ml.py`)**:
   - Leak-free lag, rolling, and cyclical feature generation.
   - 12 serialized Champion models (`models/champion/`) for $t+1\text{h}, t+3\text{h}, t+6\text{h}, t+24\text{h}$.
   - For Kharagpur, **`HistGradientBoostingRegressor`** is already trained and proven champion for $h=1, 3, 6$ hours, achieving $R^2 > 0.94-0.99$ and Danger Alert Recall $> 93\%$.
4. **Early Warning System (`src/warning_engine.py`)**:
   - Evaluates multi-tier risk: IMD Heat Wave / Severe Heat Wave, NOAA Heat Index, OSHA/ISO 7243 WBGT, and Critical Wet-Bulb limits ($T_{wb} \ge 30^\circ\text{C}$ / $35^\circ\text{C}$).
   - Produces human-interpretable rationale and action directives.
5. **Backend Microservice Architecture (`src/api_server.py`)**:
   - Asynchronous FastAPI server with CORS, in-memory caching, sub-25ms response latencies, and 9 passing unit tests.
6. **Frontend Web Application (`frontend/`)**:
   - Modern Vite + React UI, glassmorphic design system (`index.css`), pure SVG psychrometric chart with ASHRAE 55 comfort envelope, 72h trend charts, and on-demand calculation modal.

### 1.2 What Needs Modification
1. **Spatial Representation**: Current backend treats Kharagpur as a single geographical point (`22.3149, 87.3105`). It must be upgraded to serve a spatial dataset of IIT Kharagpur campus buildings, roads, open grounds, and vegetation precincts.
2. **Backend API Endpoints**: Add endpoints to serve campus GeoJSON features, building metadata, spatially resolved microclimate estimates, and scenario simulations.
3. **Frontend Dashboard Layout**: Introduce a prominent, interactive **Campus Map Component** (Leaflet / GeoJSON) alongside the existing psychrometric and trend charts.

### 1.3 What Needs to be Added
1. **Campus Spatial Model**: Digital footprint dataset of IIT Kharagpur buildings, halls of residence, academic complexes, open grounds, and green cover.
2. **Microclimate Spatial Downscaling / Estimation Engine**: Scientifically defensible model translating regional meteorological data (NASA/IMD) into building-level microclimate variations based on physical surface attributes (albedo, vegetation fraction, building density, solar exposure).
3. **Vulnerability Layer**: Assessment of human exposure duration, population density, and building vulnerability (e.g. non-AC hostels vs AC labs).
4. **Mitigation / What-If Scenario Engine**: Simulation of interventions (cool roofs, +20% tree canopy, reflective pavements) inspired by the UNSW Performance Index.

---

## 2. UNSW FEATURES TO ADAPT VS. UNNECESSARY FEATURES

The UNSW research project (High Performance Architecture / Prof. Mattheos Santamouris) and the Urban Heat Island Mitigation Performance Index evaluate urban overheating against four explicit objectives: **Outdoor Thermal Comfort, Health Risks, Energy Demand, and Water Demand**.

| UNSW Concept | Relevant to IIT Kharagpur? | Feasible in BTP? | Priority | Adaptation Strategy for IIT KGP |
| :--- | :--- | :--- | :--- | :--- |
| **Precinct/Building-Level Heat Mapping** | **YES** | **YES** | **Critical** | Map IIT KGP into individual academic departments, hostels, libraries, and open stadiums. |
| **Outdoor Thermal Comfort (WBGT/UTCI/HI)** | **YES** | **YES** | **Critical** | Calculate thermal comfort indices for each campus zone using our validated Phase 3 engine. |
| **Health & Heat Vulnerability Index** | **YES** | **YES** | **High** | Combine environmental heat stress with student/worker exposure (e.g., PAN loop hostels, athletic fields, construction sites). |
| **Mitigation What-If Scenarios (Cool Roofs, Trees)** | **YES** | **YES** | **High** | Model how reflective roofs or tree canopy expansion near hostels reduces localized Heat Index and WBGT. |
| **Evidence-Based Decision Support & Diagnosis** | **YES** | **YES** | **High** | Automatically rank hottest buildings and explain *why* they are hot (e.g., high impervious surface, zero canopy). |
| **Energy Demand Modeling** | Potentially | Simplified Proxy | Medium | Use Cooling Degree Hours (CDH) proxy rather than complex dynamic building energy simulations (EnergyPlus). |
| **Water Demand of Green Infrastructure** | Potentially | Qualitative | Low/Med | Estimate irrigation trade-offs of vegetation cooling. |
| **Full 3D City CAD Engine / CFD Simulation** | Unnecessary | Excessive | Omit / 2.5D | A high-performance 2D/2.5D GIS map is scientifically defensible; CFD simulation for 2,100 acres cannot run real-time in a web app. |

---

## 3. PROPOSED DATA ARCHITECTURE FOR IIT KHARAGPUR

We establish a clear, multi-tiered data schema distinguishing **Verified Real Data** from **Modelled Estimates**:

```
[ Tier 1: Real Sourced Meteorological Telemetry ]
  - NASA POWER Hourly Reanalysis & IMD Kharagpur Climatological Normals
  - Regional Dry-Bulb Temp, Relative Humidity, Wind Speed, Solar Irradiance, Surface Pressure

[ Tier 2: Verified Campus Spatial Footprints & GIS ]
  - Verified IIT KGP Campus Boundary (~2,100 acres, Paschim Medinipur)
  - 25+ Key Landmark Footprints (Main Building, Nalanda, Takshashila, Halls of Residence, Gymkhana, Stadiums)
  - Land Cover Attributes: Surface type (Asphalt, Concrete, Grass, Dense Canopy, Water), Albedo (alpha), Sky View Factor (SVF)

[ Tier 3: Scientific Microclimate Spatial Engine (Modelled) ]
  - Physics-based spatial delta equations calculating building-specific T_db, RH, and Solar Exposure
  - Derived thermal indices: WBGT, Heat Index, Wet-Bulb for each building

[ Tier 4: AI/ML Multi-Horizon Prediction ]
  - Champion HistGradientBoosting model forecasting regional conditions -> propagated spatially to all buildings

[ Tier 5: Decision Support & Mitigation Simulation ]
  - Baseline vs. Intervention Scenarios (+20% canopy, cool roofs alpha=0.8, misting)
```

---

## 4. SCIENTIFIC SPATIAL MODELLING APPROACH

### The Problem:
We have regional meteorological observations (NASA/IMD at Kharagpur station), but cannot pretend to have 500 physical weather stations installed on every rooftop.

### Scientifically Defensible Solution (Local Climate Zone & Microclimate Physics):
We implement a **Local Microclimate Perturbation Model** grounded in published urban climatology literature (Oke 1988, Stewart & Oke 2012 LCZ, Santamouris et al. 2018):
$$\Delta T_{micro, i} = f(\text{Albedo}_i, \text{Vegetation\_Fraction}_i, \text{Impervious\_Fraction}_i, \text{Solar\_Exposure}_i, \text{Anthropogenic\_Heat}_i)$$

1. **Solar & Surface Radiation Excess**:
   - Areas with low albedo ($\alpha \sim 0.15$, e.g., asphalt roads and parking lots) absorb high solar radiation, heating ambient air during midday ($+1.0^\circ\text{C}$ to $+2.5^\circ\text{C}$ above regional baseline).
2. **Vegetative Evaporative Cooling (Park Cool Island effect)**:
   - Areas with high tree canopy cover (e.g., Nehru/Patel lush green zones, campus woodlands) experience localized evaporative cooling ($-1.0^\circ\text{C}$ to $-2.2^\circ\text{C}$, $+5\%$ RH).
3. **Thermal Inertia & Anthropogenic Density**:
   - Dense multistory complexes (Nalanda, Main Building) exhibit thermal storage and air conditioning heat rejection.
4. **Transparent Labeling**:
   - The UI explicitly marks building values as **"Modelled Microclimate Estimate (LCZ-physics based)"**, while the campus baseline is labeled **"Measured Regional Station Observation"**.

---

## 5. SCIENTIFIC RISKS & MITIGATIONS

1. **Risk 1: False Claim of Micro-Sensor Measurement**:
   - *Mitigation*: The UI and API must explicitly distinguish:
     - **Measured**: Regional NASA/IMD station data.
     - **Modelled**: Building-level microclimate estimates.
     - **Calculated**: Thermodynamic indices (WBGT, Heat Index).
     - **Predicted**: Machine learning forecasts.
2. **Risk 2: Spatial Overfitting or Arbitrary Numbers**:
   - *Mitigation*: Microclimate deltas must be bounded within scientifically verified ranges (e.g., maximum UHI delta in Kharagpur $\le +3.5^\circ\text{C}$ based on tropical UHI literature).
3. **Risk 3: Heavy GIS Libraries Slowing Down Dashboard**:
   - *Mitigation*: Use lightweight GeoJSON structures rendered via Leaflet or high-performance SVG maps, ensuring smooth 60fps pan/zoom.

---

## 6. PRIORITIZED IMPLEMENTATION ROADMAP

We will proceed through the 16 incremental steps requested:
- **STEP 1 (Current)**: Project Audit & UNSW-Inspired Architecture Foundation. (Complete)
- **STEP 2**: Research and compile verified IIT KGP spatial/building landmarks and attributes.
- **STEP 3**: Build structured IIT KGP GeoJSON dataset with verified coordinates and physical surface properties.
- **STEP 4**: Integrate interactive campus GIS map into the frontend (pan, zoom, layer controls).
- **STEP 5**: Add building selection and interactive inspector panel.
- **STEP 6**: Implement spatial environmental estimation engine (downscaling physics).
- **STEP 7**: Implement building-level heatmap layer switching (Temperature, Heat Index, WBGT, Wet-Bulb).
- **STEP 8**: Integrate spatial AI multi-horizon predictions ($t+1\text{h}, t+3\text{h}, t+6\text{h}, t+24\text{h}$).
- **STEP 9**: Add campus heat-risk ranking table with explainable sorting.
- **STEP 10**: Add time-based diurnal heatmap slider (08:00 to 18:00).
- **STEP 11**: Add extreme heat-wave event analysis module.
- **STEP 12**: Add campus vulnerability & exposure assessment layer.
- **STEP 13**: Add mitigation & "What-If" scenario simulation engine (Cool Roofs, Canopy Increase).
- **STEP 14**: Investigate 2.5D building extrusion visualization.
- **STEP 15**: Complete automated test suite and scientific validation.
- **STEP 16**: Final UI/UX polish, performance optimization, and viva demonstration preparation.

---

## 7. AUTOMATED TEST PLAN FOR NEW CAPABILITIES

| Test ID | Target Component | Input | Expected Output | Verification Tool |
| :--- | :--- | :--- | :--- | :--- |
| **TEST-KGP-1** | Spatial GeoJSON | `data/iit_kgp_campus.geojson` | Valid GeoJSON containing $\ge 20$ campus landmarks with type, coordinates, and surface properties | Python `geojson` / `json` validator |
| **TEST-KGP-2** | Spatial API | `GET /api/campus/buildings` | HTTP 200 with FeatureCollection within bounding box $[22.30, 87.29]$ to $[22.33, 87.33]$ | FastAPI TestClient |
| **TEST-KGP-3** | Downscaling Model | Regional $T=40^\circ\text{C}, RH=50\%$ | Asphalt area $T > 41^\circ\text{C}$; Dense canopy $T < 39^\circ\text{C}$; thermodynamic ordering preserved | Unit test |
| **TEST-KGP-4** | Spatial Heatmap API | `GET /api/campus/heatmap?metric=wbgt` | Returns building-specific WBGT values and risk categories | FastAPI TestClient |
| **TEST-KGP-5** | Map Component | Render React Map | Leaflet map mounts, loads tiles, and displays color-coded polygons | Headless / Vitest & Browser |
| **TEST-KGP-6** | Building Click | Click "Main Building" | Detail panel opens showing $T, RH, WBGT, HI$, risk level, and context | React UI state test |
| **TEST-KGP-7** | Campus Ranking | `GET /api/campus/ranking` | Sorted array of buildings from highest to lowest heat stress with rationale | API unit test |
| **TEST-KGP-8** | Mitigation Engine | POST intervention: `+20% tree canopy` | Recomputed microclimate shows physically bounded temperature drop ($\sim 0.5-1.5^\circ\text{C}$) | Model unit test |
| **TEST-KGP-9** | Time Animation | Query hour 14:00 vs 08:00 | Diurnal heating shows higher thermal stress across all buildings at midday | Time series validation |
| **TEST-KGP-10**| End-to-End Pipeline | Campus Telemetry $\to$ Downscaling $\to$ AI Forecast $\to$ Map UI | Complete interactive flow functions with zero console errors | E2E integration test |

---

## 8. RECOMMENDED NEXT STEP

Proceed to **STEP 2**: Research, compile, and structure the verified spatial building dataset for IIT Kharagpur (including coordinates, building types, areas, and environmental surface contexts).
