# IIT Kharagpur Campus-Scale Microclimate Mapping & Heat-Risk Decision-Support System
## BTP Thesis & System Operational Manual
**Supervisor**: Prof. Chirodeep Bakli, Department of Mechanical Engineering / School of Energy Science and Engineering, IIT Kharagpur  
**Academic Context**: Bachelor of Technology Project (BTP) — AI-Based Microclimate Prediction and Advanced Warning System for Thermal Comfort and Heat Waves  

---

## 1. Executive Summary & Research Motivation

Rapid urbanization, localized land-use modifications, and rising frequencies of compound humid heat waves present critical physiological hazards to dense academic institutions in tropical zones. While standard regional meteorological observations (e.g., IMD synoptic stations or satellite reanalysis) provide coarse regional baselines, they fail to resolve localized thermal heterogeneity across complex institutional microclimates.

This system delivers a **physics-informed, AI-driven, campus-scale microclimate digital twin and heat-risk decision-support platform for IIT Kharagpur (2,100 acres)**. Adapted from the **UNSW High Performance Architecture Urban Heat Island Mitigation Performance Index** (Prof. M. Santamouris et al.), the platform couples:
1. Empirical microclimate downscaling derived from Local Climate Zones (LCZ) and urban morphological parameters.
2. AI-driven multi-horizon temporal forecasting (+1h, +3h, +6h, +24h) utilizing trained champion regressors.
3. Multi-dimensional Heat Vulnerability Index (HVI) modeling integrating environmental exposure, demographic sensitivity, and air-conditioning adaptive deficit.
4. What-If Urban Cooling Mitigation modeling (Cool Roofs, Urban Forestry, Permeable Pavers, and Comprehensive Green Masterplan).

---

## 2. Theoretical Formulation & Governing Equations

### 2.1 Microclimate Downscaling Formulation
For every campus landmark $i \in \{1, \dots, 24\}$, the localized dry-bulb air temperature $T_{\text{local}, i}$ is modeled as a thermodynamic perturbation from the regional background temperature $T_{\text{regional}}$:

$$T_{\text{local}, i} = T_{\text{regional}} + \Delta T_{\text{micro}, i}$$

where the microclimate delta $\Delta T_{\text{micro}, i}$ is governed by physical surface envelope parameters:

$$\Delta T_{\text{micro}, i} = \text{clamp}\left( (0.30 - \alpha_i) \cdot 2.5 - (f_{v, i} - 0.25) \cdot 2.2 + (f_{i, i} - 0.50) \cdot 1.5 + (\text{SVF}_i - 0.70) \cdot 0.8, \, -3.0, \, +3.5 \right)$$

- $\alpha_i \in [0.05, 0.60]$: Mean surface albedo (solar reflectance).
- $f_{v, i} \in [0.0, 1.0]$: Vegetative canopy fraction within a 100m buffer.
- $f_{i, i} \in [0.0, 1.0]$: Impervious surface fraction (asphalt/concrete thermal storage).
- $\text{SVF}_i \in [0.3, 1.0]$: Sky View Factor (diffuse and direct solar sky exposure).

### 2.2 Biometeorological Thermal Stress Indices
- **Stull (2011) Wet-Bulb Temperature ($T_{\text{wb}}$)**:
  $$T_{\text{wb}} = T \cdot \text{atan}\left(0.151977 \sqrt{RH + 8.313659}\right) + \text{atan}(T + RH) - \text{atan}(RH - 1.676331) + 0.00391838 \sqrt{RH^3} \cdot \text{atan}(0.023101 RH) - 4.686035$$
- **NOAA Rothfusz Heat Index ($HI$)**:
  Calculated using the 9-term polynomial regression with low/high humidity corrections when $T \ge 27^\circ\text{C}$.
- **Simplified Wet-Bulb Globe Temperature ($sWBGT$)**:
  $$sWBGT = 0.567 \cdot T + 0.393 \cdot e_a + 3.94$$
  where $e_a = \frac{RH}{100} \cdot 6.105 \exp\left(\frac{17.27 \cdot T}{237.7 + T}\right)$ is actual vapor pressure in hPa.

### 2.3 Multi-Dimensional Heat Vulnerability Index (HVI)
$$\text{HVI}_i = 0.40 \cdot \text{HEI}_i + 0.30 \cdot \text{DSI}_i + 0.30 \cdot \text{ADI}_i$$
- **Hazard Exposure Index ($\text{HEI}$)**: Normalized function of local $HI$ and $sWBGT$.
- **Demographic Sensitivity Index ($\text{DSI}$)**: Weighted by student footfall density (Very High = 100, High = 75, Medium = 50, Low = 25).
- **Adaptive Deficit Index ($\text{ADI}$)**: Weighted by $(1.0 - \text{AC Penetration}_i)$ and lack of natural vegetative shade.

---

## 3. Spatial Dataset: 24 Verified IIT Kharagpur Landmarks

The system maps 24 verified landmarks spanning academic, residential, recreational, and infrastructural precincts:

| ID | Landmark Name | Category | Albedo ($\alpha$) | Veg Fraction ($f_v$) | Imp Fraction ($f_i$) | SVF | AC Pen |
|---|---|---|---|---|---|---|---|
| `nalanda_complex` | Nalanda Classroom Complex | Academic | 0.30 | 0.20 | 0.80 | 0.78 | 0.95 |
| `main_building` | Main Academic Building & Tower | Heritage/Admin | 0.28 | 0.35 | 0.65 | 0.70 | 0.65 |
| `central_library` | Central Library | Academic | 0.32 | 0.30 | 0.70 | 0.72 | 0.90 |
| `tikka_lake_zone` | Tikka Lake & Wetland Zone | Eco/Water | 0.15 | 0.75 | 0.25 | 0.88 | 0.00 |
| `scholars_avenue` | Scholars Avenue Main Corridor | Road/Corridor | 0.12 | 0.15 | 0.85 | 0.85 | 0.00 |
| `technology_market` | Tech Market Commercial Hub | Commercial | 0.20 | 0.10 | 0.90 | 0.68 | 0.20 |
| `bc_roy_hospital` | B. C. Roy Technology Hospital | Medical | 0.32 | 0.35 | 0.65 | 0.72 | 0.85 |
| `central_workshop` | Central Industrial Workshops | Industrial | 0.18 | 0.08 | 0.92 | 0.75 | 0.10 |
| `step_complex` | STEP & Incubation Park | Innovation | 0.30 | 0.25 | 0.75 | 0.76 | 0.80 |
| `nehru_museum` | Nehru Museum of Science & Tech | Heritage | 0.28 | 0.40 | 0.60 | 0.65 | 0.40 |
| *(+14 Halls of Residence)* | RP, RK, Azad, Patel, Nehru, LLR, MMM, etc. | Residential | 0.22–0.26 | 0.28–0.45 | 0.55–0.72 | 0.62–0.74 | 0.10–0.25 |

---

## 4. Software Architecture & API Specifications

```
  +-------------------------------------------------------------------------+
  |                   React 19 + Leaflet Interactive SPA                   |
  |  - Dark-mode OSM Tile Basemap (No API key required)                    |
  |  - Building Inspector Panel (Real-time microclimate & envelope)        |
  |  - Heatmap Thematic Layer Switcher (HI, Twb, Delta-T, HVI)              |
  |  - 24-Hour Diurnal Timeline Scrubber & Animation Engine                |
  |  - Campus Risk Ranking Table & Heat Wave Stress Testing               |
  |  - What-If Urban Cooling Mitigation Engine (UNSW Index)                |
  +-------------------------------------------------------------------------+
                                      | HTTP REST
                                      v
  +-------------------------------------------------------------------------+
  |                         FastAPI Backend (Port 8000)                     |
  |  GET /api/campus/buildings           GET /api/campus/building/{id}      |
  |  GET /api/campus/microclimate/current GET /api/campus/forecast/{horizon} |
  |  GET /api/campus/diurnal             GET /api/campus/heatwave           |
  |  GET /api/campus/vulnerability       GET /api/campus/mitigation         |
  +-------------------------------------------------------------------------+
                                      |
         +----------------------------+----------------------------+
         v                                                         v
+-----------------------------------+             +-----------------------------------+
|  Physics & Downscaling Engines    |             |   Pre-Trained AI Champion Models  |
|  - Scientific psychrometrics      |             |  - Multi-Horizon Regressors       |
|  - Empirical UNSW UHI models      |             |  - Ridge & HistGradientBoosting   |
|  - Multi-dimensional HVI          |             |  - Feature lag engineering        |
+-----------------------------------+             +-----------------------------------+
```

---

## 5. Viva Voce Defense Guide & Expected Questions

### Q1: What makes this approach distinct from standard regional weather forecasting?
**Answer**: Regional forecasts (IMD or NASA POWER) provide a single synoptic coordinate for all of Kharagpur. However, urban surface morphology creates localized variations: dark asphalt on Scholars Avenue stores sensible heat creating positive thermal deltas ($+1.8^\circ\text{C}$), whereas Tikka Lake wetlands provide evaporative cooling ($-1.5^\circ\text{C}$). Our platform bridges this scale gap using empirical physics downscaling coupled with AI temporal inference.

### Q2: Why is Stull’s Wet-Bulb equation included alongside NOAA Heat Index?
**Answer**: While NOAA Heat Index evaluates human perceived heat under shade, Wet-Bulb Temperature ($T_{\text{wb}}$) represents the thermodynamic physical limit of evaporative cooling via human sweating. Stull’s formulation accurately evaluates high-humidity tropical conditions where $T_{\text{wb}} \ge 30^\circ\text{C}$ leads to acute thermal exhaustion and $T_{\text{wb}} \ge 35^\circ\text{C}$ marks the theoretical upper limit for human survivability.

### Q3: How do you justify the academic validity of the simulated microclimate values without 24 on-site weather stations?
**Answer**: Academic integrity is preserved through explicit tier labeling:
1. Observational data is labeled **"Ground-Truth Observed"**.
2. Downscaled building values are explicitly labeled **"Modelled / Estimated (Physics-Downscaled)"**.
3. Scenarios are labeled **"Modelled / Scenario Simulation (UNSW Performance Index)"**.
The equations enforce empirical conservation and are grounded in published peer-reviewed urban climatology (Santamouris et al., Oke's Local Climate Zones, and ASHRAE Fundamentals).

### Q4: How does the What-If Mitigation Engine quantify benefits?
**Answer**: It models urban interventions as physical changes to the surface envelope ($\Delta \alpha$, $\Delta f_v$, $\Delta f_i$, $\Delta \text{SVF}$) and recalculates localized energy balances. It quantifies ambient cooling ($\Delta T_{\text{cooling}}$), avoided apparent stress ($\Delta HI$), vulnerability reduction ($\Delta HVI$), and estimated percentage cooling energy savings using Cooling Degree Hours (CDH) proxies.

---

## 6. How to Run & Operate the System

### 6.1 Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Node.js 18+ and npm

### 6.2 Launch Backend Server
```bash
python -m uvicorn src.api_server:app --host 127.0.0.1 --port 8000
```
Interactive API documentation: `http://127.0.0.1:8000/docs`

### 6.3 Launch Frontend Client
```bash
cd frontend
npm run dev
```
Open browser at: `http://127.0.0.1:5173`

### 6.4 Execute Automated Academic Test Suite
```bash
python -c "import sys; sys.path.insert(0, '.'); import tests.test_campus_e2e_suite as t; t.run_all_e2e_tests()"
```
Expected output: **11/11 TESTS PASSED SUCCESSFULLY**.
