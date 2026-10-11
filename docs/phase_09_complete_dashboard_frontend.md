# Phase 9 — Complete Dashboard Frontend Report
**Project**: AI Based Dashboard Development for Microclimate Prediction and Advanced Warning System for Thermal Comfort / Heat Waves  
**Supervisor**: Prof. Chirodeep Bakli  
**Milestone**: Phase 9 Technical Documentation  

---

## 1. Scope & Design Philosophy
In Phase 9, we built the complete, responsive web dashboard using **React + Vite** and **Vanilla CSS**.
The user interface adheres to strict academic and aesthetic design standards:
- **Clean, Modern Glassmorphism**: Tailored HSL dark palette (`#0a0f1d`, `#111827`) with glass blur filters and crisp border contrasts.
- **Scientific Explainability Over Gimmicks**: Every number is accompanied by units, standard thermodynamic labels ($T_{db}, T_{wb}, T_{dp}, W, h$), and citation references.
- **High-Performance Visualizations**: Pure SVG-rendered psychrometric charts and multi-parameter time series without heavy external visualization bundle overhead.

---

## 2. Implemented Dashboard Modules

### 2.1 Station Selector & Operational Header
- Real-time station monitoring dedicated exclusively to **IIT Kharagpur campus microclimate** with real-time state fetching.
- Project metadata branding highlighting supervisor and thesis context.

### 2.2 Synthesized Warning Alert Banner
- Dynamic priority-coded alert banners (`NORMAL`, `CAUTION`, `EXTREME CAUTION`, `DANGER`, `EXTREME DANGER`, `CRITICAL EMERGENCY`).
- Live display of primary trigger statements and the **Dominant Risk Factor** (e.g., *"Dry Ambient Convection"* vs *"Moisture Evaporation Impedance"*).

### 2.3 Key Environmental Telemetry Grid
- Six real-time thermodynamic metric cards:
  1. **Dry-Bulb Temperature ($T_{db}$)**
  2. **Relative Humidity ($RH\%$)**
  3. **Wet-Bulb Temperature ($T_{wb}$)** with evaporative danger highlighting ($>30^\circ\text{C}$)
  4. **NOAA Heat Index ($HI$)**
  5. **Simplified WBGT ($\text{sWBGT}$)**
  6. **Humidity Ratio ($W$, in $\text{g/kg}$)**

### 2.4 Multi-Horizon AI Forecast Section
- 4-card forecast deck showing predicted values for **$t+1\text{h}$**, **$t+3\text{h}$**, **$t+6\text{h}$**, and **$t+24\text{h}$**.
- Displays predicted Temperature, predicted Humidity, champion model family (`Ridge` / `HistGradientBoosting`), and projected future warning tier.

### 2.5 Interactive Psychrometric Chart (`PsychrometricChart.jsx`)
- Complete SVG psychrometric coordinate representation:
  - $0^\circ\text{C}$ to $50^\circ\text{C}$ on X-axis, $0$ to $32\text{ g/kg}$ on Y-axis.
  - Saturation line ($100\%\text{ RH}$) in cyan.
  - Intermediate RH isopleths ($10\% - 90\%$).
  - **ASHRAE 55 Summer Thermal Comfort Polygon** in highlighted translucent green.
  - **7-Day Historical Scatter Points** colored by Heat Index severity.
  - **Animated Pulsing Radar Marker** pinpointing current operating microclimate state.

### 2.6 72-Hour Temporal Diurnal Trajectory (`TrendChart.jsx`)
- Multi-trace time series chart displaying concurrent evolution of NOAA Heat Index, Dry-Bulb Temperature, and Wet-Bulb Temperature against the IMD $45^\circ\text{C}$ severe heat threshold.

### 2.7 Interactive On-Demand Thermodynamic Calculator
- Sliders for Temperature ($0-50^\circ\text{C}$) and Relative Humidity ($5-100\%$).
- Evaluates states instantly via the backend `/api/calculate` endpoint, enabling professors and viva evaluators to test hypothetical scenarios.

### 2.8 Scientific Methodology Reference Drawer
- Tabulated official threshold standards and literature citations (IMD, NOAA, Stull 2011, BoM sWBGT, ASHRAE 55).

---

## 3. Frontend Build & Quality Verification
- Build tool: **Vite 8.3.2**.
- Output verification: `npm run build` executed with exit code 0.
- Production bundle compiled into `frontend/dist/` (JavaScript 73.6 KB gzipped, CSS 1.66 KB gzipped).
