import React from 'react';

/**
 * Multi-parameter Temporal Trend Viewer.
 * Plots last 72 hours of Dry-Bulb Temperature, Heat Index, and Wet-Bulb.
 */
export default function TrendChart({ series }) {
  if (!series || series.length === 0) {
    return <div style={{ color: '#64748b', textAlign: 'center', padding: '3rem' }}>No trend series data available.</div>;
  }

  const width = 580;
  const height = 360;
  const padding = { top: 25, right: 20, bottom: 45, left: 45 };

  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const yMin = 10;
  const yMax = 50;

  const scaleX = (i) => padding.left + (i / (series.length - 1)) * plotWidth;
  const scaleY = (val) => padding.top + plotHeight - ((val - yMin) / (yMax - yMin)) * plotHeight;

  const makeLinePath = (key) => {
    return series
      .map((d, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(i).toFixed(1)} ${scaleY(d[key]).toFixed(1)}`)
      .join(' ');
  };

  return (
    <div style={{ width: '100%' }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', height: 'auto', background: '#090e1a', borderRadius: '10px' }}
      >
        {/* Horizontal grid lines */}
        {[20, 30, 40, 50].map((v) => (
          <g key={`grid-y-${v}`}>
            <line
              x1={padding.left}
              y1={scaleY(v)}
              x2={padding.left + plotWidth}
              y2={scaleY(v)}
              stroke="rgba(255,255,255,0.06)"
              strokeDasharray="3 3"
            />
            <text
              x={padding.left - 6}
              y={scaleY(v) + 3}
              fill="#94a3b8"
              fontSize="10"
              textAnchor="end"
              fontFamily="Inter, sans-serif"
            >
              {v}°C
            </text>
          </g>
        ))}

        {/* IMD 45°C Heat wave line */}
        <line
          x1={padding.left}
          y1={scaleY(45)}
          x2={padding.left + plotWidth}
          y2={scaleY(45)}
          stroke="rgba(239, 68, 68, 0.5)"
          strokeDasharray="4 2"
        />

        {/* Series Lines */}
        <path d={makeLinePath('heat_index_c')} fill="none" stroke="#ef4444" strokeWidth="2.2" />
        <path d={makeLinePath('temperature_c')} fill="none" stroke="#f59e0b" strokeWidth="1.8" />
        <path d={makeLinePath('wet_bulb_c')} fill="none" stroke="#06b6d4" strokeWidth="1.6" />

        {/* Axes */}
        <line
          x1={padding.left}
          y1={padding.top + plotHeight}
          x2={padding.left + plotWidth}
          y2={padding.top + plotHeight}
          stroke="rgba(255,255,255,0.2)"
        />
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={padding.top + plotHeight}
          stroke="rgba(255,255,255,0.2)"
        />

        {/* X Axis Time Labels (sampled) */}
        {[0, Math.floor(series.length / 3), Math.floor((2 * series.length) / 3), series.length - 1].map((idx) => {
          const item = series[idx];
          if (!item) return null;
          const dateStr = item.timestamp.split('T')[0] || item.timestamp.substring(5, 10);
          return (
            <text
              key={`x-lbl-${idx}`}
              x={scaleX(idx)}
              y={padding.top + plotHeight + 18}
              fill="#94a3b8"
              fontSize="9"
              textAnchor="middle"
              fontFamily="Inter, sans-serif"
            >
              {dateStr}
            </text>
          );
        })}
      </svg>

      {/* Legend */}
      <div style={{ display: 'flex', gap: '1.2rem', justifyContent: 'center', marginTop: '0.6rem', fontSize: '0.8rem', color: '#94a3b8' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{ width: 12, height: 3, background: '#ef4444' }}></span> NOAA Heat Index
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{ width: 12, height: 2, background: '#f59e0b' }}></span> Dry-Bulb Temp (T_db)
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{ width: 12, height: 2, background: '#06b6d4' }}></span> Wet-Bulb Temp (T_wb)
        </span>
      </div>
    </div>
  );
}
