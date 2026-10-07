import React, { useState, useEffect } from 'react';
import PsychrometricChart from './components/PsychrometricChart';
import TrendChart from './components/TrendChart';
import CampusMap from './components/CampusMap';
import BuildingInspector from './components/BuildingInspector';
import CampusRiskRanking from './components/CampusRiskRanking';
import HeatWaveScenarioView from './components/HeatWaveScenarioView';
import CampusVulnerabilityLayer from './components/CampusVulnerabilityLayer';
import CampusMitigationView from './components/CampusMitigationView';

const API_BASE = 'http://127.0.0.1:8000/api';

export default function App() {
  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState('new_delhi');
  const [selectedBuildingId, setSelectedBuildingId] = useState('nalanda_complex');
  const [currentData, setCurrentData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [psychroData, setPsychroData] = useState(null);
  const [campusMicroclimate, setCampusMicroclimate] = useState(null);
  const [loading, setLoading] = useState(true);

  // Custom Calculator State
  const [calcTemp, setCalcTemp] = useState(42.0);
  const [calcRH, setCalcRH] = useState(40.0);
  const [calcResult, setCalcResult] = useState(null);
  const [calcLoading, setCalcLoading] = useState(false);

  // Fetch campus microclimate for ranking table
  useEffect(() => {
    fetch(`${API_BASE}/campus/microclimate/current`)
      .then((res) => res.json())
      .then((data) => setCampusMicroclimate(data))
      .catch((err) => console.error('Error fetching campus microclimate for ranking:', err));
  }, []);

  // Fetch initial station registry
  useEffect(() => {
    fetch(`${API_BASE}/stations`)
      .then((res) => res.json())
      .then((data) => {
        setStations(data);
        if (data.length > 0) setSelectedStation(data[0].id);
      })
      .catch((err) => console.error('Error fetching stations:', err));
  }, []);

  // Fetch station telemetry and visualizer data
  useEffect(() => {
    if (!selectedStation) return;
    setLoading(true);

    Promise.all([
      fetch(`${API_BASE}/current/${selectedStation}`).then((r) => r.json()),
      fetch(`${API_BASE}/forecast/${selectedStation}`).then((r) => r.json()),
      fetch(`${API_BASE}/history/${selectedStation}?days=3`).then((r) => r.json()),
      fetch(`${API_BASE}/psychrometrics/${selectedStation}`).then((r) => r.json()),
    ])
      .then(([current, forecast, history, psychro]) => {
        setCurrentData(current);
        setForecastData(forecast);
        setHistoryData(history);
        setPsychroData(psychro);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error loading dashboard data:', err);
        setLoading(false);
      });
  }, [selectedStation]);

  // Handle Interactive Calculator Submission
  const handleCalculate = () => {
    setCalcLoading(true);
    fetch(`${API_BASE}/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        temperature_c: parseFloat(calcTemp),
        relative_humidity_pct: parseFloat(calcRH),
        location_key: selectedStation,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        setCalcResult(data);
        setCalcLoading(false);
      })
      .catch((err) => {
        console.error('Calculation error:', err);
        setCalcLoading(false);
      });
  };

  useEffect(() => {
    handleCalculate();
  }, [selectedStation]);

  const statusObj = currentData?.status;
  const thermo = statusObj?.thermodynamic_state;
  const overallColor = statusObj?.overall_color || '#10b981';

  return (
    <div>
      {/* Header */}
      <header className="app-header">
        <div className="header-title-group">
          <div>
            <h1 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f8fafc' }}>
              Microclimate Intelligence & Thermal Warning Dashboard
            </h1>
            <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
              Bachelor Thesis Project (BTP) — Supervisor: Prof. Chirodeep Bakli
            </p>
          </div>
          <span className="badge-tag">AI-POWERED</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          <label style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Monitoring Station:</label>
          <select
            className="station-select"
            value={selectedStation}
            onChange={(e) => setSelectedStation(e.target.value)}
          >
            {stations.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.climate_zone.split(' ')[0]})
              </option>
            ))}
          </select>
        </div>
      </header>

      {/* Main Container */}
      <main className="dashboard-container">
        {/* Real-time synthesized early warning alert banner */}
        {statusObj && (
          <div
            className="warning-banner glass-panel"
            style={{
              borderColor: overallColor,
              background: `linear-gradient(90deg, rgba(17, 24, 39, 0.95), ${overallColor}22)`,
            }}
          >
            <div className="banner-content">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: overallColor,
                    boxShadow: `0 0 10px ${overallColor}`,
                  }}
                ></span>
                <h2>{statusObj.overall_level}</h2>
              </div>
              <p>
                {statusObj.explainability.primary_triggers.join(' | ')}
              </p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>Dominant Risk Factor</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                {statusObj.explainability.dominant_risk_factor}
              </div>
            </div>
          </div>
        )}

        {/* Core Environmental Telemetry Cards */}
        {thermo && (
          <div className="metrics-grid">
            <div className="metric-card glass-panel">
              <span className="metric-label">Dry-Bulb Temp (T_db)</span>
              <span className="metric-value">{thermo.temperature_c}°C</span>
              <span className="metric-sub">Ambient air at 2m height</span>
            </div>

            <div className="metric-card glass-panel">
              <span className="metric-label">Relative Humidity</span>
              <span className="metric-value">{thermo.relative_humidity_pct}%</span>
              <span className="metric-sub">Moisture fraction</span>
            </div>

            <div className="metric-card glass-panel">
              <span className="metric-label">Wet-Bulb Temp (T_wb)</span>
              <span className="metric-value" style={{ color: thermo.wet_bulb_c >= 30 ? '#ef4444' : '#06b6d4' }}>
                {thermo.wet_bulb_c}°C
              </span>
              <span className="metric-sub">Stull (2011) Evaporative Limit</span>
            </div>

            <div className="metric-card glass-panel">
              <span className="metric-label">NOAA Heat Index</span>
              <span className="metric-value" style={{ color: thermo.heat_index_c >= 39 ? '#ef4444' : '#f59e0b' }}>
                {thermo.heat_index_c}°C
              </span>
              <span className="metric-sub">Rothfusz Apparent Heat</span>
            </div>

            <div className="metric-card glass-panel">
              <span className="metric-label">Simplified WBGT</span>
              <span className="metric-value">{thermo.swbgt_c}°C</span>
              <span className="metric-sub">BoM Outdoor Heat Stress</span>
            </div>

            <div className="metric-card glass-panel">
              <span className="metric-label">Humidity Ratio (W)</span>
              <span className="metric-value">{thermo.humidity_ratio_g_kg} g/kg</span>
              <span className="metric-sub">ASHRAE Psychrometrics</span>
            </div>
          </div>
        )}

        {/* Multi-Horizon AI Forecast Section */}
        {forecastData && (
          <section className="forecast-section glass-panel">
            <div className="section-header">
              <div>
                <h3 className="section-title">AI Multi-Horizon Forecast & Projected Risk</h3>
                <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                  Model inference using location-trained champion regressors (Ridge / HistGradientBoosting)
                </p>
              </div>
            </div>

            <div className="forecast-cards-container">
              {['1', '3', '6', '24'].map((h) => {
                const item = forecastData.forecasts[`t_plus_${h}h`];
                if (!item) return null;
                return (
                  <div key={h} className="forecast-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
                        Horizon: +{h} Hour{h === '1' ? '' : 's'}
                      </span>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '0.15rem 0.5rem',
                          borderRadius: '4px',
                          backgroundColor: item.warning_color,
                          color: '#ffffff',
                        }}
                      >
                        {item.warning_level}
                      </span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.4rem' }}>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Predicted Temp</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'monospace' }}>
                          {item.predicted_temperature_c}°C
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Predicted RH</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'monospace' }}>
                          {item.predicted_relative_humidity_pct}%
                        </div>
                      </div>
                    </div>

                    <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: '0.2rem' }}>
                      Model: {item.model_architecture}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* IIT Kharagpur Campus Spatial Microclimate Map & Inspector */}
        <section style={{ marginBottom: '1.5rem' }}>
          <CampusMap
            selectedBuildingId={selectedBuildingId}
            onSelectBuilding={(id) => setSelectedBuildingId(id)}
          />

          <BuildingInspector
            buildingId={selectedBuildingId}
            onClose={() => setSelectedBuildingId(null)}
          />

          <CampusRiskRanking
            buildings={campusMicroclimate?.buildings}
            selectedBuildingId={selectedBuildingId}
            onSelectBuilding={(id) => setSelectedBuildingId(id)}
          />

          <HeatWaveScenarioView
            selectedBuildingId={selectedBuildingId}
            onSelectBuilding={(id) => setSelectedBuildingId(id)}
          />

          <CampusVulnerabilityLayer
            selectedBuildingId={selectedBuildingId}
            onSelectBuilding={(id) => setSelectedBuildingId(id)}
          />

          <CampusMitigationView />
        </section>

        {/* 2-Column Scientific Visualizers Grid */}
        <div className="charts-grid">
          {/* Interactive Psychrometric Chart */}
          <div className="chart-panel glass-panel">
            <div className="section-header">
              <div>
                <h3 className="section-title">Interactive Psychrometric Chart</h3>
                <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                  Carrier / ASHRAE coordinates at standard atmospheric pressure (1013.25 hPa)
                </p>
              </div>
            </div>
            <PsychrometricChart
              psychroData={psychroData}
              currentPoint={psychroData?.current_point}
            />
          </div>

          {/* Temporal Trends */}
          <div className="chart-panel glass-panel">
            <div className="section-header">
              <div>
                <h3 className="section-title">72-Hour Microclimate Diurnal Trajectory</h3>
                <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                  Concurrent evolution of Dry-Bulb, NOAA Heat Index, and Wet-Bulb
                </p>
              </div>
            </div>
            <TrendChart series={historyData?.series} />
          </div>
        </div>

        {/* Custom On-Demand Thermodynamic Calculator */}
        <section className="glass-panel" style={{ padding: '1.5rem' }}>
          <div className="section-header">
            <div>
              <h3 className="section-title">On-Demand Physical & Biometeorological Calculator</h3>
              <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                Interactive thesis demonstration tool to test arbitrary environmental states
              </p>
            </div>
          </div>

          <div className="calculator-panel">
            <div className="calc-input-group">
              <div className="calc-slider-group">
                <div className="calc-slider-header">
                  <span>Dry-Bulb Temperature: {calcTemp}°C</span>
                  <span style={{ color: '#94a3b8' }}>[0°C to 50°C]</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="50"
                  step="0.5"
                  value={calcTemp}
                  onChange={(e) => setCalcTemp(e.target.value)}
                />
              </div>

              <div className="calc-slider-group">
                <div className="calc-slider-header">
                  <span>Relative Humidity: {calcRH}%</span>
                  <span style={{ color: '#94a3b8' }}>[5% to 100%]</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="100"
                  step="1"
                  value={calcRH}
                  onChange={(e) => setCalcRH(e.target.value)}
                />
              </div>

              <button className="btn-primary" onClick={handleCalculate} disabled={calcLoading}>
                {calcLoading ? 'Evaluating...' : 'Re-Evaluate Thermodynamic State'}
              </button>
            </div>

            {calcResult && (
              <div style={{ background: '#090e1a', padding: '1.25rem', borderRadius: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Evaluated Warning Level</span>
                  <span
                    style={{
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      padding: '0.2rem 0.6rem',
                      borderRadius: '4px',
                      backgroundColor: calcResult.overall_color,
                      color: '#ffffff',
                    }}
                  >
                    {calcResult.overall_level}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginTop: '1rem' }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Heat Index</span>
                    <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>
                      {calcResult.thermodynamic_state.heat_index_c}°C
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Wet-Bulb (Twb)</span>
                    <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>
                      {calcResult.thermodynamic_state.wet_bulb_c}°C
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Dew Point (Tdp)</span>
                    <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>
                      {calcResult.thermodynamic_state.dew_point_c}°C
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Simplified WBGT</span>
                    <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>
                      {calcResult.thermodynamic_state.swbgt_c}°C
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '0.8rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                  <strong>Trigger Rationale: </strong>
                  {calcResult.explainability.primary_triggers[0]}
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Methodology & Standards Reference Table */}
        <section className="audit-drawer glass-panel">
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.5rem' }}>
            Scientific Methodology & Threshold Standards
          </h3>
          <p>
            This system enforces published thermodynamic equations and official biometeorological alert guidelines.
            Forecasts are generated by strictly evaluating physically grounded champion regressors.
          </p>

          <table className="audit-table">
            <thead>
              <tr>
                <th>Standard / Index</th>
                <th>Source Citation</th>
                <th>Key Equations / Critical Action Thresholds</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>IMD Heat Wave</td>
                <td>India Meteorological Department</td>
                <td>Plains base T_max ≥ 40°C; Departure ≥ +4.5°C (Heat Wave), Departure &gt; +6.4°C (Severe Heat Wave)</td>
              </tr>
              <tr>
                <td>NOAA Heat Index</td>
                <td>Rothfusz (1990), NWS SR 90-23</td>
                <td>Caution (27-32°C), Extreme Caution (32-39°C), Danger (39-51°C), Extreme Danger (≥51°C)</td>
              </tr>
              <tr>
                <td>Wet-Bulb Limit</td>
                <td>Stull (2011), J. Appl. Meteorol.</td>
                <td>Twb ≥ 30°C: Severe impairment; Twb ≥ 35°C: Theoretical upper threshold for human survivability</td>
              </tr>
              <tr>
                <td>Simplified WBGT</td>
                <td>Australian Bureau of Meteorology</td>
                <td>sWBGT = 0.567·T_db + 0.393·e_a + 3.94; ISO 7243 action threshold at 32.2°C</td>
              </tr>
            </tbody>
          </table>
        </section>
      </main>
    </div>
  );
}
