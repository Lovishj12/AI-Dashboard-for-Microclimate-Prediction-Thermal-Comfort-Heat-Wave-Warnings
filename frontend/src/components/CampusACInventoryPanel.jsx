import React, { useState, useEffect } from 'react';

/**
 * CampusACInventoryPanel
 * 
 * Engineering Thesis Component:
 * Building-Level Air Conditioning (AC) Inventory & Thermodynamic Waste Heat Emission Analysis
 * for IIT Kharagpur Campus.
 * 
 * Incorporates:
 * 1. Confirmed vs Documented vs Estimated evidence tiers.
 * 2. Thermodynamic energy balance: Q_reject = Q_cooling + P_electric = Q_cooling * (1 + 1/COP).
 * 3. Part-Load Ratio (PLR) operational scenario selector (Peak, Nominal, Reduced, Zero).
 * 4. Ambient-dependent COP derating curve.
 * 5. Transparent data provenance (e-Tenders, HMC rules, ECBC benchmarks).
 */
export default function CampusACInventoryPanel({ onSelectBuilding, selectedBuildingId }) {
  const [scenario, setScenario] = useState('nominal');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterTier, setFilterTier] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    fetch(`http://127.0.0.1:8000/api/campus/ac-inventory?scenario=${scenario}`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch AC inventory');
        return res.json();
      })
      .then((json) => {
        if (isMounted) {
          setData(json);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error('Error fetching AC inventory:', err);
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [scenario]);

  const buildings = data?.buildings || [];

  const filteredBuildings = buildings.filter((b) => {
    const matchesTier = filterTier === 'all' || b.evidence_tier.toLowerCase() === filterTier.toLowerCase();
    const matchesSearch = !searchQuery || b.building_name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTier && matchesSearch;
  });

  return (
    <div
      style={{
        background: '#0d1527',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '12px',
        padding: '1.25rem',
        marginTop: '1.5rem',
        boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
      }}
    >
      {/* Header with Title and Scientific Callout */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.2rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '1.3rem' }}>❄️</span>
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.01em' }}>
              Building-Level AC Inventory & Outdoor Waste-Heat Emissions
            </h3>
            <span
              style={{
                fontSize: '0.68rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                padding: '2px 8px',
                borderRadius: '4px',
                background: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.3)',
              }}
            >
              First Law Thermodynamic Balance
            </span>
          </div>
          <p style={{ margin: '0.3rem 0 0 0', fontSize: '0.8rem', color: '#94a3b8', maxWidth: '820px', lineHeight: '1.4' }}>
            Quantifies building-wise cooling capacity, electrical power input, and outdoor sensible heat rejection ($Q_{`\\text{reject}`} = Q_{`\\text{cooling}`} + P_{`\\text{electric}`}$) across 24 campus precincts. Differentiates verified institutional records from ECBC 2017 benchmark estimates.
          </p>
        </div>

        {/* Operating Scenario Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255, 255, 255, 0.03)', padding: '0.35rem 0.6rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>Operating State:</span>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            style={{
              background: '#0a0f1d',
              color: '#f59e0b',
              border: '1px solid rgba(245, 158, 11, 0.4)',
              borderRadius: '6px',
              padding: '0.25rem 0.6rem',
              fontSize: '0.78rem',
              fontWeight: 700,
              cursor: 'pointer',
              outline: 'none',
            }}
          >
            <option value="peak">Peak Heat Wave (0.95 PLR)</option>
            <option value="nominal">Nominal Operating (0.70 PLR)</option>
            <option value="reduced">Reduced Off-Peak (0.25 PLR)</option>
            <option value="zero">Night / Offline (0.00 PLR)</option>
          </select>
        </div>
      </div>

      {/* Campus Summary KPI Banner */}
      {data && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
            gap: '0.9rem',
            marginBottom: '1.25rem',
          }}
        >
          {/* Card 1: Active Heat Rejection */}
          <div style={{ background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.25)', borderRadius: '10px', padding: '0.85rem 1rem' }}>
            <div style={{ fontSize: '0.72rem', color: '#f59e0b', fontWeight: 700, textTransform: 'uppercase' }}>
              Active Heat Rejection (MW)
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.2rem' }}>
              {data.campus_summary.total_outdoor_heat_rejection_megawatts?.toFixed(2) || (data.campus_summary.total_outdoor_heat_rejection_kw / 1000).toFixed(2)} MW
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.15rem' }}>
              {data.campus_summary.total_outdoor_heat_rejection_kw?.toLocaleString()} kW rejected to campus canopy
            </div>
          </div>

          {/* Card 2: Installed Cooling TR */}
          <div style={{ background: 'rgba(56, 189, 248, 0.08)', border: '1px solid rgba(56, 189, 248, 0.25)', borderRadius: '10px', padding: '0.85rem 1rem' }}>
            <div style={{ fontSize: '0.72rem', color: '#38bdf8', fontWeight: 700, textTransform: 'uppercase' }}>
              Total Rated Cooling (TR)
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.2rem' }}>
              {data.campus_summary.total_installed_cooling_capacity_tr?.toLocaleString()} TR
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.15rem' }}>
              Equivalent to {((data.campus_summary.total_installed_cooling_capacity_tr * 3.51685) / 1000).toFixed(1)} MW thermal cooling
            </div>
          </div>

          {/* Card 3: Active Electrical Load */}
          <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: '10px', padding: '0.85rem 1rem' }}>
            <div style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 700, textTransform: 'uppercase' }}>
              Active Electrical Load (MW)
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.2rem' }}>
              {(data.campus_summary.active_electrical_input_kw / 1000).toFixed(2)} MW
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.15rem' }}>
              At ambient T_db = {data.operating_scenario?.ambient_air_temp_c || 35.0}°C (COP derated)
            </div>
          </div>

          {/* Card 4: Inventory Units Breakdown */}
          <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', padding: '0.85rem 1rem' }}>
            <div style={{ fontSize: '0.72rem', color: '#cbd5e1', fontWeight: 700, textTransform: 'uppercase' }}>
              Inventory Counts
            </div>
            <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.4rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#10b981', background: 'rgba(16, 185, 129, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>
                {data.campus_summary.total_ac_units_confirmed} Confirmed
              </span>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f59e0b', background: 'rgba(245, 158, 11, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>
                {data.campus_summary.total_ac_units_estimated} Estimated
              </span>
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.35rem' }}>
              Top rejection: {data.campus_summary.top_heat_rejecting_building?.name || 'Nalanda Complex'}
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.8rem', marginBottom: '0.9rem' }}>
        <div style={{ display: 'flex', gap: '0.4rem' }}>
          {['all', 'verified', 'documented', 'estimated'].map((tier) => (
            <button
              key={tier}
              onClick={() => setFilterTier(tier)}
              style={{
                background: filterTier === tier ? '#38bdf8' : 'rgba(255,255,255,0.04)',
                color: filterTier === tier ? '#0a0f1d' : '#94a3b8',
                border: filterTier === tier ? 'none' : '1px solid rgba(255,255,255,0.08)',
                padding: '0.3rem 0.7rem',
                borderRadius: '6px',
                fontSize: '0.74rem',
                fontWeight: 700,
                cursor: 'pointer',
                textTransform: 'capitalize',
              }}
            >
              {tier}
            </button>
          ))}
        </div>

        <input
          type="text"
          placeholder="Filter buildings..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            background: '#0a0f1d',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '6px',
            color: '#f8fafc',
            padding: '0.3rem 0.7rem',
            fontSize: '0.76rem',
            outline: 'none',
            minWidth: '180px',
          }}
        />
      </div>

      {/* Building Breakdown Table */}
      <div style={{ overflowX: 'auto', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: 'rgba(255,255,255,0.03)', color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <th style={{ padding: '0.6rem 0.8rem' }}>Building Precinct</th>
              <th style={{ padding: '0.6rem 0.8rem' }}>Category</th>
              <th style={{ padding: '0.6rem 0.8rem' }}>Evidence Tier</th>
              <th style={{ padding: '0.6rem 0.8rem', textAlign: 'right' }}>Installed TR</th>
              <th style={{ padding: '0.6rem 0.8rem', textAlign: 'right' }}>Active Elec (kW)</th>
              <th style={{ padding: '0.6rem 0.8rem', textAlign: 'right' }}>Q_reject (kW)</th>
              <th style={{ padding: '0.6rem 0.8rem', textAlign: 'right' }}>Heat Flux (W/m²)</th>
              <th style={{ padding: '0.6rem 0.8rem' }}>Source / Provenance</th>
            </tr>
          </thead>
          <tbody>
            {filteredBuildings.map((b) => {
              const isSelected = selectedBuildingId === b.building_id;
              const tierColor =
                b.evidence_tier === 'Verified'
                  ? '#10b981'
                  : b.evidence_tier === 'Documented'
                  ? '#60a5fa'
                  : '#f59e0b';

              return (
                <tr
                  key={b.building_id}
                  onClick={() => onSelectBuilding && onSelectBuilding(b.building_id)}
                  style={{
                    borderBottom: '1px solid rgba(255,255,255,0.04)',
                    background: isSelected ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                    cursor: 'pointer',
                    transition: 'background 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'rgba(255,255,255,0.02)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <td style={{ padding: '0.6rem 0.8rem', fontWeight: 600, color: isSelected ? '#38bdf8' : '#f8fafc' }}>
                    {b.building_name}
                  </td>
                  <td style={{ padding: '0.6rem 0.8rem', color: '#cbd5e1' }}>{b.category || 'Academic / Campus'}</td>
                  <td style={{ padding: '0.6rem 0.8rem' }}>
                    <span
                      style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        backgroundColor: `${tierColor}20`,
                        color: tierColor,
                        border: `1px solid ${tierColor}40`,
                      }}
                    >
                      {b.evidence_tier}
                    </span>
                  </td>
                  <td style={{ padding: '0.6rem 0.8rem', textAlign: 'right', color: '#f8fafc' }}>
                    {b.cooling_capacity_tons_tr ?? 0} TR
                  </td>
                  <td style={{ padding: '0.6rem 0.8rem', textAlign: 'right', color: '#38bdf8', fontWeight: 600 }}>
                    {(b.electrical_input_kw ?? 0).toFixed(1)} kW
                  </td>
                  <td style={{ padding: '0.6rem 0.8rem', textAlign: 'right', color: '#f59e0b', fontWeight: 700 }}>
                    {(b.heat_rejection_kw ?? 0).toFixed(1)} kW
                  </td>
                  <td style={{ padding: '0.6rem 0.8rem', textAlign: 'right', color: '#ec4899', fontWeight: 600 }}>
                    {(b.anthropogenic_flux_wm2 ?? 0).toFixed(1)} W/m²
                  </td>
                  <td style={{ padding: '0.6rem 0.8rem', color: '#64748b', fontSize: '0.72rem', maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {b.source_document || 'ECBC 2017 Benchmark'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Thesis Footnote on Microclimate Coupling */}
      <div
        style={{
          marginTop: '0.9rem',
          padding: '0.7rem 0.9rem',
          borderRadius: '8px',
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          fontSize: '0.74rem',
          color: '#94a3b8',
          lineHeight: '1.4',
        }}
      >
        <strong style={{ color: '#cbd5e1' }}>Scientific Rigor Note: </strong>
        Waste-heat emissions from building condensers do not directly translate into proportional local temperature increases. Outdoor canopy warming is modulated by local wind dilution [W_attenuation = 1 / (1 + 0.35 * wind_speed)], urban canopy height, and rooftop boundary layer ventilation. Microclimate anomaly models cap anthropogenic coupling (Delta T_anthro &lt;= 0.85°C) to prevent unphysical temperature divergence.
      </div>
    </div>
  );
}
