import React, { useState, useEffect } from 'react';

const INTERVENTIONS = [
  {
    id: 'cool_roofs',
    name: 'High-Albedo Cool Roofs',
    tagline: 'Roof solar reflectance α=0.70',
    icon: '🏢',
    accent: '#38bdf8'
  },
  {
    id: 'tree_canopy_expansion',
    name: 'Canopy Expansion (+25%)',
    tagline: 'Urban tree shade & evapotranspiration',
    icon: '🌳',
    accent: '#4ade80'
  },
  {
    id: 'permeable_reflective_pavements',
    name: 'Permeable Pavers Retrofit',
    tagline: 'Pavement α=0.40 & evaporative retention',
    icon: '🛣️',
    accent: '#fbbf24'
  },
  {
    id: 'comprehensive_green_infrastructure',
    name: 'UNSW Masterplan (Combined)',
    tagline: 'Synergistic Cool Roofs + Trees + Pavers',
    icon: '🌿',
    accent: '#a855f7'
  }
];

export default function CampusMitigationView() {
  const [activeIntervention, setActiveIntervention] = useState('comprehensive_green_infrastructure');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch(`http://127.0.0.1:8000/api/campus/mitigation?intervention_type=${activeIntervention}`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [activeIntervention]);

  return (
    <div className="card" style={{ marginTop: '1.5rem', background: '#0f172a', border: '1px solid #1e293b' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.2rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.4rem' }}>🛠️</span>
            <h3 style={{ margin: 0, fontSize: '1.25rem', color: '#f8fafc', fontWeight: 700 }}>
              What-If Urban Cooling Mitigation Engine
            </h3>
            <span style={{
              background: 'rgba(56, 189, 248, 0.15)',
              color: '#38bdf8',
              fontSize: '0.72rem',
              padding: '2px 8px',
              borderRadius: '4px',
              fontWeight: 600,
              border: '1px solid rgba(56, 189, 248, 0.3)'
            }}>
              UNSW Performance Index Framework
            </span>
          </div>
          <p style={{ margin: '4px 0 0', fontSize: '0.82rem', color: '#94a3b8' }}>
            Simulate physical interventions (cool roofs, urban forestry, permeable pavers) to compute microclimate cooling, Heat Index relief, and HVAC energy conservation.
          </p>
        </div>

        {/* Intervention Tabs */}
        <div style={{ display: 'flex', gap: '6px', background: '#020617', padding: '4px', borderRadius: '8px', border: '1px solid #1e293b' }}>
          {INTERVENTIONS.map(iv => {
            const isActive = activeIntervention === iv.id;
            return (
              <button
                key={iv.id}
                onClick={() => setActiveIntervention(iv.id)}
                style={{
                  background: isActive ? iv.accent : 'transparent',
                  color: isActive ? '#0f172a' : '#94a3b8',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '6px 12px',
                  fontSize: '0.78rem',
                  fontWeight: isActive ? 700 : 500,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.2s ease'
                }}
              >
                <span>{iv.icon}</span>
                <span>{iv.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {loading && (
        <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
          Evaluating thermodynamic mitigation efficacy across 24 campus zones...
        </div>
      )}

      {error && (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', borderRadius: '6px', border: '1px solid #ef4444' }}>
          Failed to load mitigation scenario: {error}
        </div>
      )}

      {data && !loading && (
        <div>
          {/* Summary KPIs */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            marginBottom: '1.2rem'
          }}>
            <div style={{ background: '#1e293b', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #38bdf8' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Mean Ambient Cooling</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#38bdf8', marginTop: '4px' }}>
                -{data.intervention.mean_temperature_reduction_c.toFixed(2)} °C
              </div>
              <div style={{ fontSize: '0.75rem', color: '#cbd5e1', marginTop: '4px' }}>Campus-wide air temp reduction</div>
            </div>

            <div style={{ background: '#1e293b', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #4ade80' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Mean Heat Index Relief</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#4ade80', marginTop: '4px' }}>
                -{data.intervention.mean_heat_index_relief_c.toFixed(2)} °C
              </div>
              <div style={{ fontSize: '0.75rem', color: '#cbd5e1', marginTop: '4px' }}>Avoided apparent thermal stress</div>
            </div>

            <div style={{ background: '#1e293b', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #fbbf24' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>HVAC Energy Savings</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fbbf24', marginTop: '4px' }}>
                ~{data.intervention.average_hvac_energy_reduction_pct.toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: '#cbd5e1', marginTop: '4px' }}>Avoided cooling degree hours</div>
            </div>

            <div style={{ background: '#1e293b', padding: '1rem', borderRadius: '8px', borderLeft: '4px solid #c084fc' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Top Beneficiary Zone</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#c084fc', marginTop: '4px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {data.intervention.top_beneficiary_building}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#cbd5e1', marginTop: '4px' }}>
                Max cooling: -{data.intervention.maximum_cooling_achieved_c.toFixed(2)} °C
              </div>
            </div>
          </div>

          {/* Description banner */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid #334155',
            padding: '0.8rem 1rem',
            borderRadius: '6px',
            marginBottom: '1.2rem',
            fontSize: '0.82rem',
            color: '#cbd5e1'
          }}>
            <strong style={{ color: '#f8fafc' }}>{data.intervention.name}: </strong>
            {data.intervention.description}
          </div>

          {/* Detailed Building Impact Table */}
          <div style={{ overflowX: 'auto', maxHeight: '380px', borderRadius: '8px', border: '1px solid #1e293b' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#020617', color: '#94a3b8', borderBottom: '1px solid #1e293b', position: 'sticky', top: 0, zIndex: 1 }}>
                  <th style={{ padding: '10px 12px' }}>Rank</th>
                  <th style={{ padding: '10px 12px' }}>Campus Landmark</th>
                  <th style={{ padding: '10px 12px' }}>Category</th>
                  <th style={{ padding: '10px 12px' }}>Baseline T</th>
                  <th style={{ padding: '10px 12px' }}>Mitigated T</th>
                  <th style={{ padding: '10px 12px', color: '#38bdf8' }}>ΔT Cooling</th>
                  <th style={{ padding: '10px 12px', color: '#4ade80' }}>ΔHI Relief</th>
                  <th style={{ padding: '10px 12px', color: '#c084fc' }}>HVI Saved</th>
                  <th style={{ padding: '10px 12px', color: '#fbbf24' }}>Energy Saved</th>
                </tr>
              </thead>
              <tbody>
                {data.buildings.map((b, idx) => (
                  <tr key={b.id} style={{
                    borderBottom: '1px solid #1e293b',
                    background: idx % 2 === 0 ? 'transparent' : 'rgba(30, 41, 59, 0.3)'
                  }}>
                    <td style={{ padding: '8px 12px', color: '#64748b', fontWeight: 600 }}>#{idx + 1}</td>
                    <td style={{ padding: '8px 12px', color: '#f8fafc', fontWeight: 600 }}>{b.name}</td>
                    <td style={{ padding: '8px 12px', color: '#94a3b8' }}>{b.category}</td>
                    <td style={{ padding: '8px 12px', color: '#cbd5e1' }}>{b.unmitigated.temperature_c.toFixed(1)}°C</td>
                    <td style={{ padding: '8px 12px', color: '#cbd5e1' }}>{b.mitigated.temperature_c.toFixed(1)}°C</td>
                    <td style={{ padding: '8px 12px', color: '#38bdf8', fontWeight: 700 }}>
                      -{b.net_cooling_benefit.temperature_reduction_c.toFixed(2)}°C
                    </td>
                    <td style={{ padding: '8px 12px', color: '#4ade80', fontWeight: 700 }}>
                      -{b.net_cooling_benefit.heat_index_reduction_c.toFixed(2)}°C
                    </td>
                    <td style={{ padding: '8px 12px', color: '#c084fc', fontWeight: 600 }}>
                      -{b.net_cooling_benefit.vulnerability_points_saved.toFixed(1)} pts
                    </td>
                    <td style={{ padding: '8px 12px', color: '#fbbf24', fontWeight: 600 }}>
                      ~{b.net_cooling_benefit.cooling_degree_hours_saved_pct.toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ marginTop: '0.8rem', fontSize: '0.72rem', color: '#64748b', textAlign: 'right' }}>
            Theoretical physical mitigation models adapted from M. Santamouris et al. (UNSW Sydney / High Performance Architecture UHI Performance Index).
          </div>
        </div>
      )}
    </div>
  );
}
