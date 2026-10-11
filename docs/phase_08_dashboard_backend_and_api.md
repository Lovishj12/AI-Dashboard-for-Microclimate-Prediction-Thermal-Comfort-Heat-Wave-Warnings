# Phase 8 — Dashboard Backend & API Report
**Project**: AI Based Dashboard Development for Microclimate Prediction and Advanced Warning System for Thermal Comfort / Heat Waves  
**Supervisor**: Prof. Chirodeep Bakli  
**Milestone**: Phase 8 Technical Documentation  

---

## 1. Scope & Architecture
In Phase 8, we engineered the backend microservice layer using **FastAPI** (`src/api_server.py`). The backend serves as the bridge connecting data ingestion, thermodynamic physics, machine learning inference, and the upcoming user interface.

### Architecture Highlights
- **High Performance & Asynchronous**: Built with FastAPI and Starlette, with in-memory caching for sub-25ms response latencies.
- **Strict Data Validation**: Implemented Pydantic models for incoming payload validation and typing.
- **Comprehensive CORS Support**: Cross-Origin Resource Sharing enabled for modern decoupled frontend frameworks.
- **RESTful Endpoints**: Modular endpoints designed for specific dashboard sections.

---

## 2. API Specifications & Endpoints

| Endpoint | HTTP Method | Description | Primary Response Data |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | Service liveness, status, and station list | System health status, version, available station IDs |
| `/api/metadata` | `GET` | Scientific metadata, thresholds, references | IMD thresholds, NOAA HI ranges, OSHA WBGT limits, research citations |
| `/api/stations` | `GET` | Meteorological station registry | Names, coordinates (lat/lon), elevations, and climate zones |
| `/api/current/{station_id}` | `GET` | Current telemetry, thermodynamics, and alerts | Latest $T, RH, WS, P$, Dew Point, Wet-Bulb, Heat Index, sWBGT, synthesized warning tier |
| `/api/forecast/{station_id}` | `GET` | AI Champion multi-horizon forecast & alert projections | $t+1\text{h}, t+3\text{h}, t+6\text{h}, t+24\text{h}$ predictions, model architectures, future warning levels |
| `/api/history/{station_id}` | `GET` | Hourly time-series for trend charts | Configurable history ($1-90$ days) with full thermodynamic state records |
| `/api/psychrometrics/{station_id}` | `GET` | Psychrometric chart coordinate curves & empirical points | $10\%-100\%\text{ RH}$ curves, ASHRAE comfort polygon, 7-day empirical scatter, current operating point |
| `/api/calculate` | `POST` | Instant arbitrary state calculation | Evaluates arbitrary input $(T, RH)$ through the full thermodynamic & warning pipeline |

---

## 3. Automated Validation & Unit Test Results

All 9 endpoints were systematically validated using `TestClient` in [`tests/test_api_server.py`](file:///c:/Users/lovis/Desktop/BTP/tests/test_api_server.py):

| Test Case | Method / Endpoint | Verified Behavior | Status |
| :--- | :--- | :--- | :--- |
| `test_health_check` | `GET /api/health` | Returns `200 OK`, `status="healthy"`, and list of pilot stations | **PASSED** |
| `test_metadata` | `GET /api/metadata` | Returns official standards citations and configuration thresholds | **PASSED** |
| `test_stations_registry` | `GET /api/stations` | Returns station registry dedicated exclusively to IIT Kharagpur | **PASSED** |
| `test_current_conditions` | `GET /api/current/kharagpur` | Returns latest observation, thermodynamic state, and overall warning | **PASSED** |
| `test_forecast_endpoint` | `GET /api/forecast/kharagpur` | Produces $t+1\text{h}, t+3\text{h}, t+6\text{h}, t+24\text{h}$ AI forecast predictions | **PASSED** |
| `test_history_endpoint` | `GET /api/history/kharagpur?days=3` | Returns exact 72 hourly observations with multi-metric time series | **PASSED** |
| `test_psychrometric_chart_data` | `GET /api/psychrometrics/kharagpur` | Delivers saturation line, RH curves, ASHRAE comfort polygon, and points | **PASSED** |
| `test_calculate_endpoint` | `POST /api/calculate` | Computes arbitrary inputs ($44^\circ\text{C}, 30\%$) with complete explainability | **PASSED** |
| `test_invalid_station_404` | `GET /api/current/invalid_xyz` | Responds with standard `404 Not Found` for nonexistent stations | **PASSED** |

**Execution**: 9 tests ran in **0.246s** with zero errors.
