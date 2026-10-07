import React, { useMemo } from 'react';

/**
 * Interactive SVG-based Psychrometric Chart.
 * Maps:
 * - X-Axis: Dry-Bulb Temperature (0°C to 50°C)
 * - Y-Axis: Humidity Ratio W (0 to 32 g/kg)
 * Renders saturation curve (100% RH), intermediate RH curves,
 * ASHRAE Standard 55 summer comfort polygon,
 * 7-day empirical telemetry scatter, and current live operating point.
 */
export default function PsychrometricChart({ psychroData, currentPoint }) {
  const width = 640;
  const height = 400;
  const padding = { top: 25, right: 30, bottom: 45, left: 55 };

  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const tMin = 0;
  const tMax = 50;
  const wMin = 0;
  const wMax = 32;

  // Coordinate scales
  const scaleX = (t) => padding.left + ((t - tMin) / (tMax - tMin)) * plotWidth;
  const scaleY = (w) => padding.top + plotHeight - ((w - wMin) / (wMax - wMin)) * plotHeight;

  // Format path from array of points
  const makePath = (pts) => {
    if (!pts || pts.length === 0) return '';
    return pts
      .filter((p) => p.t >= tMin && p.t <= tMax && p.w >= wMin && p.w <= wMax)
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${scaleX(p.t).toFixed(1)} ${scaleY(p.w).toFixed(1)}`)
      .join(' ');
  };

  // ASHRAE 55 Polygon points string
  const comfortPolyStr = useMemo(() => {
    if (!psychroData?.comfort_polygon) return '';
    return psychroData.comfort_polygon
      .map((p) => `${scaleX(p.t).toFixed(1)},${scaleY(p.w).toFixed(1)}`)
      .join(' ');
  }, [psychroData]);

  return (
    <div style={{ width: '100%', position: 'relative' }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', height: 'auto', background: '#090e1a', borderRadius: '10px' }}
      >
        {/* Grid lines */}
        {[10, 20, 30, 40, 50].map((t) => (
          <line
            key={`grid-x-${t}`}
            x1={scaleX(t)}
            y1={padding.top}
            x2={scaleX(t)}
            y2={padding.top + plotHeight}
            stroke="rgba(255,255,255,0.06)"
            strokeDasharray="3 3"
          />
        ))}
        {[5, 10, 15, 20, 25, 30].map((w) => (
          <line
            key={`grid-y-${w}`}
            x1={padding.left}
            y1={scaleY(w)}
            x2={padding.left + plotWidth}
            y2={scaleY(w)}
            stroke="rgba(255,255,255,0.06)"
            strokeDasharray="3 3"
          />
        ))}

        {/* ASHRAE 55 Summer Comfort Region */}
        {comfortPolyStr && (
          <polygon
            points={comfortPolyStr}
            fill="rgba(16, 185, 129, 0.2)"
            stroke="#10b981"
            strokeWidth="1.5"
            strokeDasharray="4 2"
          />
        )}

        {/* Relative Humidity Curves */}
        {psychroData?.rh_curves &&
          Object.entries(psychroData.rh_curves).map(([key, pts]) => {
            const isSat = key === 'rh_100';
            return (
              <path
                key={key}
                d={makePath(pts)}
                fill="none"
                stroke={isSat ? '#06b6d4' : 'rgba(59, 130, 246, 0.35)'}
                strokeWidth={isSat ? '2' : '1'}
              />
            );
          })}

        {/* 7-Day Empirical Scatter Points */}
        {psychroData?.recent_points?.map((pt, i) => (
          <circle
            key={`hist-${i}`}
            cx={scaleX(pt.t)}
            cy={scaleY(pt.w)}
            r="2.5"
            fill={pt.hi >= 39 ? '#ef4444' : pt.hi >= 32 ? '#f59e0b' : '#3b82f6'}
            opacity="0.45"
          />
        ))}

        {/* Current Operating Point */}
        {currentPoint && (
          <g>
            <circle
              cx={scaleX(currentPoint.t)}
              cy={scaleY(currentPoint.w)}
              r="7"
              fill="#ec4899"
              stroke="#ffffff"
              strokeWidth="2"
            />
            <circle
              cx={scaleX(currentPoint.t)}
              cy={scaleY(currentPoint.w)}
              r="14"
              fill="none"
              stroke="#ec4899"
              strokeWidth="1.5"
              opacity="0.6"
            >
              <animate attributeName="r" values="7;18;7" dur="2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.8;0;0.8" dur="2s" repeatCount="indefinite" />
            </circle>
          </g>
        )}

        {/* Axes */}
        <line
          x1={padding.left}
          y1={padding.top + plotHeight}
          x2={padding.left + plotWidth}
          y2={padding.top + plotHeight}
          stroke="rgba(255,255,255,0.3)"
        />
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={padding.top + plotHeight}
          stroke="rgba(255,255,255,0.3)"
        />

        {/* Ticks and Labels */}
        {[0, 10, 20, 30, 40, 50].map((t) => (
          <text
            key={`lbl-x-${t}`}
            x={scaleX(t)}
            y={padding.top + plotHeight + 18}
            fill="#94a3b8"
            fontSize="10"
            textAnchor="middle"
            fontFamily="Inter, sans-serif"
          >
            {t}°C
          </text>
        ))}

        {[0, 5, 10, 15, 20, 25, 30].map((w) => (
          <text
            key={`lbl-y-${w}`}
            x={padding.left - 8}
            y={scaleY(w) + 3}
            fill="#94a3b8"
            fontSize="10"
            textAnchor="end"
            fontFamily="Inter, sans-serif"
          >
            {w}
          </text>
        ))}

        {/* Axis Titles */}
        <text
          x={padding.left + plotWidth / 2}
          y={height - 8}
          fill="#cbd5e1"
          fontSize="11"
          fontWeight="600"
          textAnchor="middle"
        >
          Dry-Bulb Temperature T_db (°C)
        </text>

        <text
          transform={`rotate(-90)`}
          x={-(padding.top + plotHeight / 2)}
          y={15}
          fill="#cbd5e1"
          fontSize="11"
          fontWeight="600"
          textAnchor="middle"
        >
          Humidity Ratio W (g/kg)
        </text>
      </svg>
      
      {/* Legend */}
      <div style={{ display: 'flex', gap: '1.2rem', justifyContent: 'center', marginTop: '0.6rem', fontSize: '0.8rem', color: '#94a3b8' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{ width: 12, height: 2, background: '#06b6d4' }}></span> 100% Saturation
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{ width: 10, height: 10, background: 'rgba(16, 185, 129, 0.3)', border: '1px solid #10b981' }}></span> ASHRAE 55 Comfort
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ec4899' }}></span> Current State
        </span>
      </div>
    </div>
  );
}
