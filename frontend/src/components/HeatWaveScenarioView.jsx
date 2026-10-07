import React, { useEffect, useState } from 'react';

export default function HeatWaveScenarioView({ onSelectBuilding, selectedBuildingId }) {
  const [activeScenario, setActiveScenario] = useState('imd_severe_heat_wave');
  const [scenarioData, setScenarioData] = useState(null);
  const [loading, setLoading] = useState(false);

  const scenarios = [
    { id: 'imd_heat_wave', label: 'IMD Heat Wave (+4.5°C)', badge: 'ADVISORY' },
    { id: 'imd_severe_heat_wave', label: 'IMD Severe Wave (+6.5°C)', badge: 'CRITICAL' },
    { id: 'humid_heat_crisis', label: 'Humid Heat Crisis (Twb Stress)', badge: 'LETHAL' },
    { id: 'dry_convective_blast', label: 'Dry Convective Blast (+7.0°C)', badge: 'DESICCATING' },
  ];

  useEffect(() => {
    setLoading(true);
    fetch(`http://127.0.0.1:8000/api/campus/heatwave?scenario_type=${activeScenario}`)
      .then((res) => res.json())
      .then((data) => {
        setScenarioData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Heat wave scenario fetch error:', err);
        setLoading(false);
      });
  }, [activeScenario]);

  const audit = scenarioData?.stress_test_audit;
  const scen = scenarioData?.scenario;

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', marginTop: '1.25rem', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.8rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                padding: '0.2rem 0.5rem',
                borderRadius: '4px',
                background: 'rgba(239, 68, 68, 0.2)',
                color: '#ef4444',
                border: '1px solid rgba(239, 68, 68, 0.4)',
              }}
            >
              Emergency Heat Wave Stress Test
            </span>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              Tier: <strong style={{ color: '#f59e0b' }}>Modelled / Scenario Simulation (IMD Criteria)</strong>
            </span>
          </div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.25rem' }}>
            Campus Severe Overheating & Wet-Bulb Stress Simulation
          </h3>
        </div>

        {/* Scenario Selector Tabs */}
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          {scenarios.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveScenario(s.id)}
              style={{
                padding: '0.3rem 0.65rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                borderRadius: '6px',
                border: activeScenario === s.id ? '1px solid #ef4444' : '1px solid rgba(255,255,255,0.08)',
                background: activeScenario === s.id ? 'rgba(239, 68, 68, 0.25)' : 'rgba(255,255,255,0.02)',
                color: activeScenario === s.id ? '#ffffff' : '#94a3b8',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div style={{ padding: '2rem', textAlign: 'center', color: '#ef4444' }}>
          Simulating campus-scale thermodynamic response to extreme heat wave...
        </div>
      )}

      {!loading && scenarioData && (
        <div>
          {/* Executive Scenario Banner */}
          <div
            style={{
              padding: '0.85rem 1rem',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.08)',
              borderLeft: '4px solid #ef4444',
              marginBottom: '1rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div>
                <strong style={{ color: '#f8fafc', fontSize: '0.9rem' }}>{scen?.name}</strong>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.15rem' }}>
                  {scen?.description}
                </p>
              </div>
              <div style={{ display: 'flex', gap: '1.2rem', textAlign: 'right' }}>
                <div>
                  <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Regional Forcing T:</span>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#ef4444', fontFamily: 'monospace' }}>
                    {scen?.regional_temperature_c}°C
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Forcing RH:</span>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#38bdf8', fontFamily: 'monospace' }}>
                    {scen?.regional_relative_humidity_pct}%
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Solar Insolation:</span>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f59e0b', fontFamily: 'monospace' }}>
                    {scen?.solar_radiation_wm2} W/m²
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Critical Threshold Audit & Action Banner */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
            {/* Box 1: Critical Wet-Bulb Breach */}
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#ef4444', textTransform: 'uppercase' }}>
                1. Stull Wet-Bulb Critical Limit (Twb &ge; 30°C)
              </span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.3rem' }}>
                {audit?.critical_twb_count} <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>/ 24 Buildings Exceeded</span>
              </div>
              <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                Exceeding 30°C Wet-Bulb impairs evaporative human thermoregulation.
              </p>
              {audit?.critical_twb_landmarks.length > 0 && (
                <div style={{ marginTop: '0.4rem', fontSize: '0.72rem', color: '#ef4444' }}>
                  Breached: {audit.critical_twb_landmarks.slice(0, 3).join(', ')}{audit.critical_twb_landmarks.length > 3 ? ` +${audit.critical_twb_landmarks.length - 3} more` : ''}
                </div>
              )}
            </div>

            {/* Box 2: Extreme Danger Heat Index Breach */}
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#881337', textTransform: 'uppercase' }}>
                2. NOAA Heat Index Extreme Danger (HI &ge; 45°C)
              </span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.3rem' }}>
                {audit?.extreme_danger_hi_count} <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>/ 24 Buildings Exceeded</span>
              </div>
              <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                Imminent risk of heat stroke, fainting, and physiological collapse.
              </p>
              {audit?.extreme_danger_hi_landmarks.length > 0 && (
                <div style={{ marginTop: '0.4rem', fontSize: '0.72rem', color: '#ec4899' }}>
                  Breached: {audit.extreme_danger_hi_landmarks.slice(0, 3).join(', ')}{audit.extreme_danger_hi_landmarks.length > 3 ? ` +${audit.extreme_danger_hi_landmarks.length - 3} more` : ''}
                </div>
              )}
            </div>

            {/* Box 3: Campus Operational Directives */}
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f59e0b', textTransform: 'uppercase' }}>
                3. Institutional Action Directive
              </span>
              <div style={{ fontSize: '0.82rem', color: '#f8fafc', fontWeight: 600, marginTop: '0.4rem', lineHeight: '1.4' }}>
                {audit?.institutional_action}
              </div>
              <div style={{ marginTop: '0.6rem', fontSize: '0.72rem', color: '#94a3b8' }}>
                Protocols: Mandatory hostel hydration stops • Cancel gym & stadium practice • Deploy misting fans at Nalanda
              </div>
            </div>
          </div>

          {/* Top 6 Stress-Tested Hotspots Quick Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.6rem' }}>
            {scenarioData.buildings.slice(0, 6).map((b, i) => (
              <div
                key={b.id}
                onClick={() => onSelectBuilding && onSelectBuilding(b.id)}
                style={{
                  padding: '0.65rem 0.8rem',
                  borderRadius: '6px',
                  background: selectedBuildingId === b.id ? 'rgba(6, 182, 212, 0.15)' : 'rgba(255,255,255,0.03)',
                  border: selectedBuildingId === b.id ? '1px solid #06b6d4' : '1px solid rgba(255,255,255,0.06)',
                  cursor: 'pointer',
                }}
              >
                <div style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Rank #{i + 1}</span>
                  <span style={{ color: b.microclimate.risk_color, fontWeight: 700 }}>{b.microclimate.heat_index_risk}</span>
                </div>
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc', marginTop: '0.15rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {b.name}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.3rem', fontSize: '0.72rem' }}>
                  <span>HI: <strong style={{ color: b.microclimate.risk_color }}>{b.microclimate.heat_index_c}°C</strong></span>
                  <span>Twb: <strong style={{ color: b.microclimate.wet_bulb_c >= 30 ? '#ef4444' : '#38bdf8' }}>{b.microclimate.wet_bulb_c}°C</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
