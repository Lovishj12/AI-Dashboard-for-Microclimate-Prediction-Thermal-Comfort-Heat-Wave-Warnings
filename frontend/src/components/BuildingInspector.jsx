import React, { useEffect, useState } from 'react';

export default function BuildingInspector({ buildingId, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!buildingId) return;
    setLoading(true);
    fetch(`http://127.0.0.1:8000/api/campus/building/${buildingId}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Building not found: ${res.status}`);
        return res.json();
      })
      .then((resData) => {
        setData(resData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Inspector error:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [buildingId]);

  if (!buildingId) return null;

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', marginTop: '1rem', border: '1px solid rgba(6, 182, 212, 0.3)' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                padding: '0.2rem 0.5rem',
                borderRadius: '4px',
                background: 'rgba(6, 182, 212, 0.15)',
                color: '#06b6d4',
                border: '1px solid rgba(6, 182, 212, 0.3)',
              }}
            >
              Precinct Heat Inspector
            </span>
            <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
              Tier: <strong style={{ color: '#f59e0b' }}>Modelled / Estimated (Physics-Downscaled)</strong>
            </span>
          </div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.3rem' }}>
            {data ? data.properties.name : 'Loading Building Profile...'}
          </h3>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
            {data?.properties.notes}
          </p>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              border: 'none',
              borderRadius: '6px',
              color: '#94a3b8',
              padding: '0.3rem 0.6rem',
              cursor: 'pointer',
              fontSize: '0.8rem',
            }}
          >
            ✕ Close
          </button>
        )}
      </div>

      {loading && (
        <div style={{ padding: '2rem', textAlign: 'center', color: '#06b6d4' }}>
          Querying downscaled microclimate & thermal vulnerability state...
        </div>
      )}

      {error && (
        <div style={{ padding: '1.5rem', textAlign: 'center', color: '#ef4444' }}>
          Failed to load building data: {error}
        </div>
      )}

      {data && !loading && (() => {
        const riskLevel = data.modelled_microclimate.risk_status[0] || 'Normal';
        const riskColor = data.modelled_microclimate.risk_status[1] || '#10b981';

        return (
        <div>
          {/* Prominent Building Active Alert Signal Banner */}
          <div
            className="alert-pulse-badge"
            style={{
              padding: '0.85rem 1.25rem',
              borderRadius: '10px',
              marginBottom: '1.25rem',
              background: `linear-gradient(90deg, rgba(15, 23, 42, 0.95), ${riskColor}30)`,
              border: `2px solid ${riskColor}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '1rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
              <span
                className="beacon-dot"
                style={{
                  width: '16px',
                  height: '16px',
                  borderRadius: '50%',
                  backgroundColor: riskColor,
                  boxShadow: `0 0 14px ${riskColor}`,
                  display: 'inline-block',
                }}
              ></span>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.74rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', fontWeight: 700 }}>
                    Active Precinct Heat Alert Signal
                  </span>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      fontWeight: 800,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      backgroundColor: riskColor,
                      color: '#ffffff',
                    }}
                  >
                    {riskLevel.toUpperCase()}
                  </span>
                </div>
                <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.15rem' }}>
                  {riskLevel === 'Danger'
                    ? `Severe Heat Wave Alert: Heat Index ${data.modelled_microclimate.heat_index_c.toFixed(1)}°C exceeds critical threshold`
                    : riskLevel === 'Extreme Caution'
                    ? `Elevated Thermal Stress Alert: Heat Index ${data.modelled_microclimate.heat_index_c.toFixed(1)}°C requires active hydration`
                    : `Normal Precinct Operating Condition: Heat Index ${data.modelled_microclimate.heat_index_c.toFixed(1)}°C`}
                </div>
                <div style={{ fontSize: '0.78rem', color: '#cbd5e1', marginTop: '0.1rem' }}>
                  {riskLevel === 'Danger'
                    ? '⚠️ Advisory: Limit continuous outdoor physical work. Hydration stations and shaded recovery zones recommended for precinct occupants.'
                    : riskLevel === 'Extreme Caution'
                    ? '⚡ Advisory: Monitor unconditioned spaces. Heat cramps and physical exhaustion possible with sustained outdoor exposure.'
                    : '✓ Advisory: Microclimate conditions remain within tolerable bioclimatic boundary.'}
                </div>
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Precinct Vulnerability</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: riskColor }}>
                {data.modelled_microclimate.vulnerability_index_score} / 100
              </div>
            </div>
          </div>

          {/* Main 3-Column Inspector Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
            {/* Column 1: Local Thermal State */}
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#06b6d4', marginBottom: '0.6rem', textTransform: 'uppercase' }}>
                1. Downscaled Microclimate
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Modelled Air Temp (T_db):</span>
                <span style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc' }}>
                  {data.modelled_microclimate.temperature_c}°C
                  <span
                    style={{
                      fontSize: '0.72rem',
                      marginLeft: '0.4rem',
                      color: data.modelled_microclimate.temperature_delta_c >= 0 ? '#ef4444' : '#10b981',
                    }}
                  >
                    ({data.modelled_microclimate.temperature_delta_c >= 0 ? '+' : ''}{data.modelled_microclimate.temperature_delta_c}°C)
                  </span>
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Rooftop / Skin LST:</span>
                <span style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f97316' }}>
                  {data.modelled_microclimate.surface_temperature_c ? `${data.modelled_microclimate.surface_temperature_c}°C` : 'N/A'}
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
                <span style={{ color: '#94a3b8' }}>Local Relative Humidity:</span>
                <strong style={{ color: '#f8fafc' }}>{data.modelled_microclimate.relative_humidity_pct}%</strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
                <span style={{ color: '#94a3b8' }}>Stull Wet-Bulb (T_wb):</span>
                <strong style={{ color: data.modelled_microclimate.wet_bulb_c >= 30 ? '#ef4444' : '#38bdf8' }}>
                  {data.modelled_microclimate.wet_bulb_c.toFixed(1)}°C
                </strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
                <span style={{ color: '#94a3b8' }}>NOAA Heat Index:</span>
                <strong style={{ color: data.modelled_microclimate.risk_status[1] }}>
                  {data.modelled_microclimate.heat_index_c.toFixed(1)}°C ({data.modelled_microclimate.risk_status[0]})
                </strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
                <span style={{ color: '#94a3b8' }}>Simplified WBGT:</span>
                <strong style={{ color: '#f8fafc' }}>{data.modelled_microclimate.swbgt_c.toFixed(1)}°C</strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginTop: '0.4rem', paddingTop: '0.4rem', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ color: '#64748b' }}>Resolution: {data.spatial_resolution || '10-30m'}</span>
                <span style={{ color: '#64748b' }}>Uncertainty: {data.uncertainty_c || '±0.75°C'}</span>
              </div>
            </div>

            {/* Column 2: Physical Microclimate Parameters */}
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#3b82f6', marginBottom: '0.6rem', textTransform: 'uppercase' }}>
                2. Surface & Built-Environment
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
                <span style={{ color: '#94a3b8' }}>Surface Solar Albedo (α):</span>
                <strong style={{ color: '#f8fafc' }}>{data.properties.albedo}</strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
                <span style={{ color: '#94a3b8' }}>Vegetation Fraction (f_v):</span>
                <strong style={{ color: '#10b981' }}>{(data.properties.vegetation_fraction * 100).toFixed(0)}%</strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
                <span style={{ color: '#94a3b8' }}>Impervious Surface (f_i):</span>
                <strong style={{ color: '#f59e0b' }}>{(data.properties.impervious_fraction * 100).toFixed(0)}%</strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
                <span style={{ color: '#94a3b8' }}>Sky View Factor (SVF):</span>
                <strong style={{ color: '#f8fafc' }}>{data.properties.sky_view_factor}</strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                <span style={{ color: '#94a3b8' }}>Footprint Area & Height:</span>
                <strong style={{ color: '#f8fafc' }}>{data.properties.area_sqm.toLocaleString()} m² • {data.properties.floors} Fl.</strong>
              </div>
            </div>

            {/* Column 3: Vulnerability & Adaptation Readiness */}
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#ec4899', marginBottom: '0.6rem', textTransform: 'uppercase' }}>
                3. Vulnerability & Exposure
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Heat Vulnerability Index:</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ec4899' }}>
                  {data.modelled_microclimate.vulnerability_index_score} / 100
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
                <span style={{ color: '#94a3b8' }}>Estimated Footfall:</span>
                <strong style={{ color: '#f8fafc' }}>{data.properties.estimated_footfall}</strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
                <span style={{ color: '#94a3b8' }}>HVAC / AC Penetration:</span>
                <strong style={{ color: data.properties.ac_penetration < 0.3 ? '#ef4444' : '#10b981' }}>
                  {(data.properties.ac_penetration * 100).toFixed(0)}% AC
                </strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                <span style={{ color: '#94a3b8' }}>Baseline Risk Category:</span>
                <span
                  style={{
                    padding: '0.1rem 0.4rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    background:
                      data.properties.vulnerability_baseline === 'Extreme' || data.properties.vulnerability_baseline === 'High'
                        ? 'rgba(239, 68, 68, 0.2)'
                        : 'rgba(16, 185, 129, 0.2)',
                    color:
                      data.properties.vulnerability_baseline === 'Extreme' || data.properties.vulnerability_baseline === 'High'
                        ? '#ef4444'
                        : '#10b981',
                  }}
                >
                  {data.properties.vulnerability_baseline}
                </span>
              </div>
            </div>
          </div>

          {/* Scientific Rationale Callout Banner */}
          <div
            style={{
              marginTop: '0.85rem',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              background: 'rgba(6, 182, 212, 0.08)',
              borderLeft: '4px solid #06b6d4',
              fontSize: '0.8rem',
              color: '#94a3b8',
              lineHeight: '1.4',
            }}
          >
            <strong style={{ color: '#f8fafc' }}>Microclimate Attribution Rationale: </strong>
            {data.scientific_rationale}
          </div>
        </div>
        );
      })()}
    </div>
  );
}
