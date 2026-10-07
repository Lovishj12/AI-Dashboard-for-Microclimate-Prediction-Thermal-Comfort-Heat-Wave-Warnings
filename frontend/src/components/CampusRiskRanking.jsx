import React, { useState } from 'react';

export default function CampusRiskRanking({ buildings, onSelectBuilding, selectedBuildingId }) {
  const [sortBy, setSortBy] = useState('heat_index'); // 'heat_index', 'vulnerability', 'temp_delta'
  const [filterCategory, setFilterCategory] = useState('all');

  if (!buildings || buildings.length === 0) return null;

  // Filter by category
  const filtered = buildings.filter((b) => {
    if (filterCategory === 'all') return true;
    return b.category.toLowerCase().includes(filterCategory.toLowerCase());
  });

  // Sort based on selected metric
  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'heat_index') {
      return b.microclimate.heat_index_c - a.microclimate.heat_index_c;
    }
    if (sortBy === 'vulnerability') {
      return b.microclimate.vulnerability_score - a.microclimate.vulnerability_score;
    }
    if (sortBy === 'temp_delta') {
      return b.microclimate.temperature_delta_c - a.microclimate.temperature_delta_c;
    }
    return 0;
  });

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', marginTop: '1.25rem' }}>
      {/* Header & Controls */}
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
                background: 'rgba(239, 68, 68, 0.15)',
                color: '#ef4444',
                border: '1px solid rgba(239, 68, 68, 0.3)',
              }}
            >
              Priority Action Hierarchy
            </span>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              UNSW UHI Ranking Diagnostic (24 Campus Landmarks)
            </span>
          </div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.25rem' }}>
            Campus Heat-Risk & Vulnerability Rankings
          </h3>
        </div>

        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Category Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem' }}>
            <span style={{ color: '#94a3b8' }}>Filter:</span>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              style={{
                background: '#0a0f1d',
                color: '#94a3b8',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '6px',
                padding: '0.25rem 0.5rem',
                fontSize: '0.75rem',
                outline: 'none',
              }}
            >
              <option value="all">All Precincts (24)</option>
              <option value="academic">Academic</option>
              <option value="hostel">Hostels (Halls)</option>
              <option value="sports">Sports / Open</option>
              <option value="nature">Water / Nature</option>
            </select>
          </div>

          {/* Sort Metric */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem' }}>
            <span style={{ color: '#94a3b8' }}>Rank By:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{
                background: '#0a0f1d',
                color: '#06b6d4',
                border: '1px solid rgba(6, 182, 212, 0.4)',
                borderRadius: '6px',
                padding: '0.25rem 0.5rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                outline: 'none',
              }}
            >
              <option value="heat_index">NOAA Heat Index (°C)</option>
              <option value="vulnerability">Heat Vulnerability Index (0-100)</option>
              <option value="temp_delta">Microclimate Delta ΔT (°C)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Interactive Ranking Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8' }}>
              <th style={{ padding: '0.5rem 0.6rem', width: '45px' }}>Rank</th>
              <th style={{ padding: '0.5rem 0.6rem' }}>Building / Spatial Precinct</th>
              <th style={{ padding: '0.5rem 0.6rem' }}>Typology</th>
              <th style={{ padding: '0.5rem 0.6rem' }}>Modelled T_db</th>
              <th style={{ padding: '0.5rem 0.6rem' }}>UHI Delta (ΔT)</th>
              <th style={{ padding: '0.5rem 0.6rem' }}>Stull Twb</th>
              <th style={{ padding: '0.5rem 0.6rem' }}>Heat Index</th>
              <th style={{ padding: '0.5rem 0.6rem' }}>HVI Score</th>
              <th style={{ padding: '0.5rem 0.6rem', textAlign: 'center' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((b, idx) => {
              const isSelected = selectedBuildingId === b.id;
              const micro = b.microclimate;
              const isTopRisk = idx < 3;

              return (
                <tr
                  key={b.id}
                  onClick={() => onSelectBuilding && onSelectBuilding(b.id)}
                  style={{
                    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                    background: isSelected
                      ? 'rgba(6, 182, 212, 0.12)'
                      : isTopRisk
                      ? 'rgba(239, 68, 68, 0.03)'
                      : 'transparent',
                    cursor: 'pointer',
                    transition: 'background 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.background = isTopRisk ? 'rgba(239, 68, 68, 0.03)' : 'transparent';
                    }
                  }}
                >
                  {/* Rank */}
                  <td style={{ padding: '0.6rem', fontWeight: 700, color: isTopRisk ? '#ef4444' : '#64748b' }}>
                    #{idx + 1}
                  </td>

                  {/* Name */}
                  <td style={{ padding: '0.6rem', fontWeight: 600, color: isSelected ? '#06b6d4' : '#f8fafc' }}>
                    {b.name}
                    {isTopRisk && (
                      <span
                        style={{
                          marginLeft: '0.4rem',
                          fontSize: '0.68rem',
                          padding: '0.1rem 0.35rem',
                          borderRadius: '3px',
                          background: 'rgba(239, 68, 68, 0.2)',
                          color: '#ef4444',
                        }}
                      >
                        HIGH ALERT
                      </span>
                    )}
                  </td>

                  {/* Category */}
                  <td style={{ padding: '0.6rem', color: '#94a3b8' }}>{b.category}</td>

                  {/* T_db */}
                  <td style={{ padding: '0.6rem', fontFamily: 'monospace' }}>
                    {micro.temperature_c}°C
                  </td>

                  {/* Delta */}
                  <td
                    style={{
                      padding: '0.6rem',
                      fontFamily: 'monospace',
                      fontWeight: 700,
                      color: micro.temperature_delta_c >= 0 ? '#ef4444' : '#10b981',
                    }}
                  >
                    {micro.temperature_delta_c >= 0 ? '+' : ''}
                    {micro.temperature_delta_c}°C
                  </td>

                  {/* Twb */}
                  <td style={{ padding: '0.6rem', fontFamily: 'monospace', color: micro.wet_bulb_c >= 30 ? '#ef4444' : '#38bdf8' }}>
                    {micro.wet_bulb_c.toFixed(1)}°C
                  </td>

                  {/* Heat Index */}
                  <td style={{ padding: '0.6rem', fontWeight: 700, color: micro.risk_color }}>
                    {micro.heat_index_c.toFixed(1)}°C
                  </td>

                  {/* HVI Score Bar */}
                  <td style={{ padding: '0.6rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div
                        style={{
                          width: '60px',
                          height: '6px',
                          background: 'rgba(255,255,255,0.1)',
                          borderRadius: '3px',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            width: `${Math.min(100, micro.vulnerability_score)}%`,
                            height: '100%',
                            background:
                              micro.vulnerability_score > 70
                                ? '#ef4444'
                                : micro.vulnerability_score > 50
                                ? '#f59e0b'
                                : '#10b981',
                          }}
                        />
                      </div>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#f8fafc' }}>
                        {micro.vulnerability_score}
                      </span>
                    </div>
                  </td>

                  {/* Focus Action */}
                  <td style={{ padding: '0.6rem', textAlign: 'center' }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onSelectBuilding) onSelectBuilding(b.id);
                      }}
                      style={{
                        padding: '0.25rem 0.6rem',
                        fontSize: '0.72rem',
                        borderRadius: '4px',
                        border: isSelected ? '1px solid #06b6d4' : '1px solid rgba(255,255,255,0.1)',
                        background: isSelected ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255,255,255,0.02)',
                        color: isSelected ? '#06b6d4' : '#94a3b8',
                        cursor: 'pointer',
                      }}
                    >
                      {isSelected ? 'Focused' : 'Inspect'}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
