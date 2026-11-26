import React, { useEffect, useState, useMemo } from 'react';
import { API_BASE } from '../config';

export default function ModeComparisonPanel({ activeMode }) {
  const [aiData, setAiData] = useState(null);
  const [litData, setLitData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAllRows, setShowAllRows] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function fetchBothModes() {
      try {
        setLoading(true);
        setError(null);
        const [aiRes, litRes] = await Promise.all([
          fetch(`${API_BASE}/campus/microclimate/current?mode=ai`),
          fetch(`${API_BASE}/campus/microclimate/current?mode=literature`),
        ]);
        if (!aiRes.ok || !litRes.ok) {
          throw new Error('Failed to fetch comparison data for both modes');
        }
        const [aiJson, litJson] = await Promise.all([aiRes.json(), litRes.json()]);
        if (!cancelled) {
          setAiData(aiJson);
          setLitData(litJson);
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchBothModes();
    return () => {
      cancelled = true;
    };
  }, [activeMode]);

  const comparisonRows = useMemo(() => {
    if (!aiData?.buildings || !litData?.buildings) return [];
    const litMap = {};
    litData.buildings.forEach((b) => {
      litMap[b.id] = b;
    });

    return aiData.buildings
      .map((aiB) => {
        const litB = litMap[aiB.id];
        if (!litB) return null;
        const aiDelta = aiB.microclimate?.temperature_delta_c ?? 0;
        const litDelta = litB.microclimate?.temperature_delta_c ?? 0;
        const diff = +(aiDelta - litDelta).toFixed(2);
        return {
          id: aiB.id,
          name: aiB.name,
          category: aiB.category,
          floors: aiB.physical_attributes?.floors ?? 3,
          albedo: aiB.physical_attributes?.albedo ?? 0.25,
          svf: aiB.physical_attributes?.sky_view_factor ?? 0.75,
          veg: aiB.physical_attributes?.vegetation_fraction ?? 0.3,
          aiDelta,
          litDelta,
          diff,
          absDiff: Math.abs(diff),
          aiTemp: aiB.microclimate?.temperature_c ?? 0,
          litTemp: litB.microclimate?.temperature_c ?? 0,
        };
      })
      .filter(Boolean)
      .sort((a, b) => b.absDiff - a.absDiff);
  }, [aiData, litData]);

  const summaryStats = useMemo(() => {
    if (!comparisonRows.length) return null;
    const meanAi =
      comparisonRows.reduce((acc, r) => acc + r.aiDelta, 0) / comparisonRows.length;
    const meanLit =
      comparisonRows.reduce((acc, r) => acc + r.litDelta, 0) / comparisonRows.length;
    const maxDiv = comparisonRows[0];
    return {
      meanAi: meanAi.toFixed(2),
      meanLit: meanLit.toFixed(2),
      meanDiff: (meanAi - meanLit).toFixed(2),
      maxDiv,
      regTemp: aiData?.regional_reference?.temperature_c,
      regRh: aiData?.regional_reference?.relative_humidity_pct,
    };
  }, [comparisonRows, aiData]);

  if (loading) {
    return (
      <section className="glass-panel" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ color: '#38bdf8', fontSize: '0.9rem' }}>
          Loading AI vs. Literature coefficient comparison...
        </div>
      </section>
    );
  }

  if (error || !summaryStats) {
    return null;
  }

  const chartRows = comparisonRows.slice(0, 8);
  const maxBarVal = Math.max(
    1.0,
    ...chartRows.map((r) => Math.max(Math.abs(r.aiDelta), Math.abs(r.litDelta)))
  );
  const tableRows = showAllRows ? comparisonRows : comparisonRows.slice(0, 8);

  return (
    <section
      className="glass-panel"
      style={{
        padding: '1.4rem',
        marginBottom: '1.5rem',
        borderRadius: '12px',
        border: '1px solid rgba(56, 189, 248, 0.25)',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1.2rem',
        }}
      >
        <div>
          <h3 className="section-title" style={{ marginBottom: '0.25rem' }}>
            📊 AI-Predicted vs. Literature Coefficients: Campus-Wide Comparison
          </h3>
          <p style={{ fontSize: '0.84rem', color: '#94a3b8', margin: 0 }}>
            Both modes use the identical live regional baseline ({summaryStats.regTemp}°C,{' '}
            {summaryStats.regRh}% RH). Differences below come purely from building-specific ML
            coefficients vs. fixed literature constants.
          </p>
        </div>
        <span
          style={{
            fontSize: '0.72rem',
            fontWeight: 700,
            padding: '4px 10px',
            borderRadius: '6px',
            background: 'rgba(139, 92, 246, 0.18)',
            color: '#c4b5fd',
            border: '1px solid rgba(139, 92, 246, 0.4)',
          }}
        >
          MODEL R² = 0.893 (MULTI-OUTPUT REGRESSOR)
        </span>
      </div>

      {/* Summary KPI Strip */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
          gap: '0.85rem',
          marginBottom: '1.4rem',
        }}
      >
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.7)',
            padding: '0.85rem 1rem',
            borderRadius: '8px',
            border: '1px solid rgba(56, 189, 248, 0.25)',
          }}
        >
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>
            Campus Mean ΔT (AI Mode)
          </div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#38bdf8', fontFamily: 'monospace' }}>
            {Number(summaryStats.meanAi) >= 0 ? '+' : ''}
            {summaryStats.meanAi}°C
          </div>
        </div>

        <div
          style={{
            background: 'rgba(15, 23, 42, 0.7)',
            padding: '0.85rem 1rem',
            borderRadius: '8px',
            border: '1px solid rgba(16, 185, 129, 0.25)',
          }}
        >
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>
            Campus Mean ΔT (Literature)
          </div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#10b981', fontFamily: 'monospace' }}>
            {Number(summaryStats.meanLit) >= 0 ? '+' : ''}
            {summaryStats.meanLit}°C
          </div>
        </div>

        <div
          style={{
            background: 'rgba(15, 23, 42, 0.7)',
            padding: '0.85rem 1rem',
            borderRadius: '8px',
            border: '1px solid rgba(251, 191, 36, 0.25)',
          }}
        >
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>
            Mean Variance (AI − Lit)
          </div>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#fbbf24', fontFamily: 'monospace' }}>
            {Number(summaryStats.meanDiff) >= 0 ? '+' : ''}
            {summaryStats.meanDiff}°C
          </div>
        </div>

        <div
          style={{
            background: 'rgba(15, 23, 42, 0.7)',
            padding: '0.85rem 1rem',
            borderRadius: '8px',
            border: '1px solid rgba(244, 63, 94, 0.25)',
          }}
        >
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>
            Highest Divergence Building
          </div>
          <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f8fafc', marginTop: '0.15rem' }}>
            {summaryStats.maxDiv.name}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#fb7185', fontFamily: 'monospace' }}>
            {summaryStats.maxDiv.diff >= 0 ? '+' : ''}
            {summaryStats.maxDiv.diff}°C difference
          </div>
        </div>
      </div>

      {/* Visual Grouped Bar Chart */}
      <div
        style={{
          background: 'rgba(7, 11, 20, 0.65)',
          padding: '1rem 1.2rem',
          borderRadius: '10px',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          marginBottom: '1.4rem',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '0.9rem',
            flexWrap: 'wrap',
            gap: '0.5rem',
          }}
        >
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0' }}>
            Top 8 Buildings by Coefficient Divergence (ΔT Anomaly Comparison)
          </span>
          <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', color: '#38bdf8' }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: '#38bdf8' }} />
              AI Coefficients ΔT
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', color: '#10b981' }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: '#10b981' }} />
              Literature Constants ΔT
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {chartRows.map((row) => {
            const aiWidth = Math.min(100, (Math.abs(row.aiDelta) / maxBarVal) * 100);
            const litWidth = Math.min(100, (Math.abs(row.litDelta) / maxBarVal) * 100);
            return (
              <div key={row.id} style={{ display: 'grid', gridTemplateColumns: '210px 1fr 75px', gap: '0.75rem', alignItems: 'center' }}>
                <div
                  style={{
                    fontSize: '0.78rem',
                    color: '#cbd5e1',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                  title={row.name}
                >
                  {row.name}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {/* AI Bar */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div
                      style={{
                        height: '8px',
                        width: `${Math.max(4, aiWidth)}%`,
                        background: 'linear-gradient(90deg, #0284c7, #38bdf8)',
                        borderRadius: '4px',
                        transition: 'width 0.4s ease',
                      }}
                    />
                    <span style={{ fontSize: '0.72rem', color: '#38bdf8', fontFamily: 'monospace' }}>
                      {row.aiDelta >= 0 ? '+' : ''}
                      {row.aiDelta}°C
                    </span>
                  </div>
                  {/* Literature Bar */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div
                      style={{
                        height: '8px',
                        width: `${Math.max(4, litWidth)}%`,
                        background: 'linear-gradient(90deg, #059669, #10b981)',
                        borderRadius: '4px',
                        transition: 'width 0.4s ease',
                      }}
                    />
                    <span style={{ fontSize: '0.72rem', color: '#10b981', fontFamily: 'monospace' }}>
                      {row.litDelta >= 0 ? '+' : ''}
                      {row.litDelta}°C
                    </span>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span
                    style={{
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      fontFamily: 'monospace',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: row.diff >= 0 ? 'rgba(56, 189, 248, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                      color: row.diff >= 0 ? '#38bdf8' : '#10b981',
                    }}
                  >
                    {row.diff >= 0 ? '+' : ''}
                    {row.diff}°C
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detailed Comparison Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.12)', color: '#94a3b8', textAlign: 'left' }}>
              <th style={{ padding: '0.6rem 0.5rem' }}>Campus Building / Precinct</th>
              <th style={{ padding: '0.6rem 0.5rem' }}>Morphology (Floors / SVF / α)</th>
              <th style={{ padding: '0.6rem 0.5rem', color: '#38bdf8' }}>AI ΔT</th>
              <th style={{ padding: '0.6rem 0.5rem', color: '#10b981' }}>Lit ΔT</th>
              <th style={{ padding: '0.6rem 0.5rem', color: '#fbbf24' }}>Variance (AI − Lit)</th>
              <th style={{ padding: '0.6rem 0.5rem' }}>AI Local Temp</th>
              <th style={{ padding: '0.6rem 0.5rem' }}>Lit Local Temp</th>
            </tr>
          </thead>
          <tbody>
            {tableRows.map((row) => (
              <tr
                key={row.id}
                style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', color: '#e2e8f0' }}
              >
                <td style={{ padding: '0.55rem 0.5rem', fontWeight: 600 }}>{row.name}</td>
                <td style={{ padding: '0.55rem 0.5rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                  {row.floors}F | SVF {row.svf} | α {row.albedo}
                </td>
                <td style={{ padding: '0.55rem 0.5rem', color: '#38bdf8', fontFamily: 'monospace', fontWeight: 700 }}>
                  {row.aiDelta >= 0 ? '+' : ''}
                  {row.aiDelta}°C
                </td>
                <td style={{ padding: '0.55rem 0.5rem', color: '#10b981', fontFamily: 'monospace', fontWeight: 700 }}>
                  {row.litDelta >= 0 ? '+' : ''}
                  {row.litDelta}°C
                </td>
                <td style={{ padding: '0.55rem 0.5rem', color: '#fbbf24', fontFamily: 'monospace', fontWeight: 700 }}>
                  {row.diff >= 0 ? '+' : ''}
                  {row.diff}°C
                </td>
                <td style={{ padding: '0.55rem 0.5rem', fontFamily: 'monospace' }}>{row.aiTemp}°C</td>
                <td style={{ padding: '0.55rem 0.5rem', fontFamily: 'monospace' }}>{row.litTemp}°C</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {comparisonRows.length > 8 && (
        <div style={{ marginTop: '0.9rem', textAlign: 'center' }}>
          <button
            onClick={() => setShowAllRows((prev) => !prev)}
            style={{
              background: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.35)',
              color: '#38bdf8',
              padding: '0.4rem 1rem',
              borderRadius: '6px',
              fontSize: '0.78rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {showAllRows
              ? 'Show Top 8 Buildings'
              : `Show All ${comparisonRows.length} Campus Buildings`}
          </button>
        </div>
      )}
    </section>
  );
}
