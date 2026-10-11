import React, { useState } from 'react';

/**
 * Multi-parameter Temporal Trend Viewer.
 * Plots continuous 72 hours of Dry-Bulb Temperature, Heat Index, and Wet-Bulb for IIT Kharagpur.
 * Fully localized to Asia/Kolkata (IST, UTC+5:30).
 */
export default function TrendChart({
  series,
  dataSource = 'live_telemetry',
  dataSourceLabel,
  timezone = 'Asia/Kolkata',
  startTimestamp,
  endTimestamp,
}) {
  const [hoverIndex, setHoverIndex] = useState(null);

  if (!series || series.length === 0) {
    return (
      <div style={{ color: '#64748b', textAlign: 'center', padding: '3.5rem 1rem' }}>
        <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>📡</div>
        <div style={{ fontSize: '0.9rem', color: '#94a3b8' }}>Continuous telemetry currently loading...</div>
        <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
          Querying IIT Kharagpur microclimate data feed
        </div>
      </div>
    );
  }

  const width = 580;
  const height = 360;
  const padding = { top: 32, right: 24, bottom: 50, left: 45 };

  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const yMin = 15;
  const yMax = 50;

  const scaleX = (i) => padding.left + (i / Math.max(1, series.length - 1)) * plotWidth;
  const scaleY = (val) => padding.top + plotHeight - ((val - yMin) / (yMax - yMin)) * plotHeight;

  const makeLinePath = (key) => {
    return series
      .map((d, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(i).toFixed(1)} ${scaleY(d[key]).toFixed(1)}`)
      .join(' ');
  };

  /**
   * Format timestamp in Asia/Kolkata time format: "DD MMM HH:mm" (e.g., "08 Oct 00:00")
   */
  const formatTickLabel = (tsStr) => {
    if (!tsStr) return '';
    try {
      // Handles both "YYYY-MM-DD HH:mm:ss" and ISO formats
      const cleanStr = tsStr.replace(' ', 'T');
      const d = new Date(cleanStr);
      if (isNaN(d.getTime())) {
        return tsStr.substring(5, 16);
      }
      return d.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      });
    } catch {
      return tsStr.substring(5, 16);
    }
  };

  // Determine tick indices for exactly 4 evenly spaced points across the timeline: start, +24h, +48h, end (+72h)
  const tickIndices = [];
  if (series.length > 0) {
    tickIndices.push(0);
    if (series.length >= 3) {
      tickIndices.push(Math.round(series.length / 3));
      tickIndices.push(Math.round((2 * series.length) / 3));
    }
    tickIndices.push(series.length - 1);
  }

  const isLive = dataSource === 'live_telemetry';
  const badgeText = isLive ? 'LIVE TELEMETRY (IST)' : 'HISTORICAL BENCHMARK';
  const badgeColor = isLive ? '#10b981' : '#f59e0b';
  const badgeBg = isLive ? 'rgba(16, 185, 129, 0.12)' : 'rgba(245, 158, 11, 0.12)';
  const badgeBorder = isLive ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)';

  const activePoint = hoverIndex !== null && series[hoverIndex] ? series[hoverIndex] : null;

  return (
    <div style={{ width: '100%' }}>
      {/* Telemetry Status Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.6rem',
          padding: '0.35rem 0.6rem',
          background: 'rgba(15, 23, 42, 0.6)',
          borderRadius: '6px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
          <span
            style={{
              fontSize: '0.68rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '12px',
              color: badgeColor,
              backgroundColor: badgeBg,
              border: `1px solid ${badgeBorder}`,
              letterSpacing: '0.4px',
            }}
          >
            ● {badgeText}
          </span>
          <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
            {series.length} Hourly Observations | Timezone: <strong style={{ color: '#cbd5e1' }}>Asia/Kolkata (UTC+5:30)</strong>
          </span>
        </div>

        <div style={{ fontSize: '0.7rem', color: '#64748b' }}>
          IIT Kharagpur (22.3149°N, 87.3105°E)
        </div>
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', height: 'auto', background: '#090e1a', borderRadius: '10px' }}
        onMouseLeave={() => setHoverIndex(null)}
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
          stroke="rgba(239, 68, 68, 0.45)"
          strokeDasharray="4 2"
        />
        <text
          x={padding.left + plotWidth - 4}
          y={scaleY(45) - 4}
          fill="rgba(239, 68, 68, 0.7)"
          fontSize="8.5"
          textAnchor="end"
          fontFamily="Inter, sans-serif"
        >
          IMD Heat Wave Threshold (45°C)
        </text>

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

        {/* Interactive Hover Vertical Cursor */}
        {activePoint && hoverIndex !== null && (
          <g>
            <line
              x1={scaleX(hoverIndex)}
              y1={padding.top}
              x2={scaleX(hoverIndex)}
              y2={padding.top + plotHeight}
              stroke="rgba(255, 255, 255, 0.35)"
              strokeDasharray="2 2"
            />
            {/* Dots on the curves */}
            <circle cx={scaleX(hoverIndex)} cy={scaleY(activePoint.heat_index_c)} r="3.5" fill="#ef4444" />
            <circle cx={scaleX(hoverIndex)} cy={scaleY(activePoint.temperature_c)} r="3.5" fill="#f59e0b" />
            <circle cx={scaleX(hoverIndex)} cy={scaleY(activePoint.wet_bulb_c)} r="3.5" fill="#06b6d4" />
          </g>
        )}

        {/* X Axis Time Labels in Asia/Kolkata */}
        {tickIndices.map((idx) => {
          const item = series[idx];
          if (!item) return null;
          const formatted = formatTickLabel(item.timestamp);
          const isFirst = idx === 0;
          const isLast = idx === series.length - 1;
          const textAnchor = isFirst ? 'start' : isLast ? 'end' : 'middle';
          const xPos = scaleX(idx);

          return (
            <text
              key={`x-lbl-${idx}`}
              x={xPos}
              y={padding.top + plotHeight + 18}
              fill="#94a3b8"
              fontSize="9"
              textAnchor={textAnchor}
              fontFamily="Inter, sans-serif"
            >
              {formatted}
            </text>
          );
        })}

        {/* Timezone label on bottom axis */}
        <text
          x={padding.left + plotWidth / 2}
          y={height - 8}
          fill="#64748b"
          fontSize="8.5"
          textAnchor="middle"
          fontFamily="Inter, sans-serif"
        >
          Timeline: 72 Hours (IST / Asia/Kolkata)
        </text>

        {/* Invisible Overlay Bars for Crisp Mouse Hover Tracking */}
        {series.map((d, i) => {
          const barW = plotWidth / series.length;
          const barX = padding.left + i * barW;
          return (
            <rect
              key={`hover-col-${i}`}
              x={barX}
              y={padding.top}
              width={barW}
              height={plotHeight}
              fill="transparent"
              style={{ cursor: 'crosshair' }}
              onMouseEnter={() => setHoverIndex(i)}
            />
          );
        })}
      </svg>

      {/* Active Point Readout / Tooltip Banner */}
      {activePoint ? (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '0.45rem',
            padding: '0.4rem 0.8rem',
            background: 'rgba(30, 41, 59, 0.7)',
            borderRadius: '6px',
            fontSize: '0.78rem',
            fontFamily: 'monospace',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <span style={{ color: '#cbd5e1' }}>
            🕒 {activePoint.timestamp} IST
          </span>
          <span style={{ color: '#ef4444' }}>
            HI: <strong>{activePoint.heat_index_c}°C</strong>
          </span>
          <span style={{ color: '#f59e0b' }}>
            T_db: <strong>{activePoint.temperature_c}°C</strong>
          </span>
          <span style={{ color: '#06b6d4' }}>
            T_wb: <strong>{activePoint.wet_bulb_c}°C</strong>
          </span>
          <span style={{ color: '#94a3b8' }}>
            RH: {activePoint.relative_humidity_pct}%
          </span>
        </div>
      ) : (
        /* Legend */
        <div
          style={{
            display: 'flex',
            gap: '1.2rem',
            justifyContent: 'center',
            marginTop: '0.55rem',
            fontSize: '0.78rem',
            color: '#94a3b8',
          }}
        >
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
      )}
    </div>
  );
}

