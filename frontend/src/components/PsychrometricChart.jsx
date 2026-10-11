import React, { useMemo } from 'react';
import { computeAirState } from '../utils/psychrometrics';

/**
 * Interactive SVG-based Psychrometric Chart.
 * Maps:
 * - X-Axis: Dry-Bulb Temperature (0°C to 50°C)
 * - Y-Axis: Humidity Ratio W (0 to 32 g/kg)
 *
 * Renders:
 * - Saturation curve (100% RH) in cyan
 * - Intermediate RH curves (10% - 90%)
 * - ASHRAE Standard 55 summer comfort polygon
 * - 7-day empirical telemetry scatter
 * - Live operating state / interactive simulated state
 * - Constant Enthalpy / Wet-Bulb guide line intersecting the active point
 * - Interactive slider controls (T_db & RH) with real-time thermodynamic state synchronization
 */
export default function PsychrometricChart({
  psychroData,
  currentPoint,
  activeState,
  sliderTemp,
  sliderRH,
  onTempChange,
  onRHChange,
  onResetToLive,
}) {
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

  // Format SVG path from array of points
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

  // Determine active point to display
  // Prioritizes activeState (from reactive sliders) over static currentPoint
  const targetPoint = useMemo(() => {
    if (activeState) {
      return {
        t: activeState.t,
        w: activeState.w,
        twb: activeState.twb,
        tdp: activeState.tdp,
        hi: activeState.hi,
        h: activeState.h,
        swbgt: activeState.swbgt,
        inComfort: activeState.inComfort,
        hiLevel: activeState.hiLevel,
        hiColor: activeState.hiColor,
      };
    }
    if (currentPoint) {
      const calc = computeAirState(currentPoint.t, 50.0); // fallback
      return {
        t: currentPoint.t,
        w: currentPoint.w,
        twb: currentPoint.twb,
        hi: currentPoint.hi,
        inComfort: calc.inComfort,
        hiColor: '#ec4899',
      };
    }
    return null;
  }, [activeState, currentPoint]);

  // Compute constant wet-bulb / enthalpy line guide through target point
  const guideLine = useMemo(() => {
    if (!targetPoint) return null;
    const { t, w, twb } = targetPoint;
    // Sloping adiabatic line: slope dw/dt is approximately -c_pa / h_fg ~= -0.24 to -0.42 g/(kg·K)
    // Using physical line passing through (t, w):
    const slope = -0.42;
    const tStart = Math.max(tMin, t - 15);
    const tEnd = Math.min(tMax, t + 15);
    const wStart = w - slope * (tStart - t);
    const wEnd = w - slope * (tEnd - t);

    return {
      x1: scaleX(tStart),
      y1: scaleY(Math.min(wMax, Math.max(wMin, wStart))),
      x2: scaleX(tEnd),
      y2: scaleY(Math.min(wMax, Math.max(wMin, wEnd))),
    };
  }, [targetPoint]);

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
      {/* Real-time Interactive Sliders Bar */}
      {onTempChange && onRHChange && (
        <div
          style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '10px',
            padding: '0.85rem 1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '0.02em' }}>
              Real-Time Psychrometric State Controller
            </span>
            {onResetToLive && (
              <button
                type="button"
                onClick={onResetToLive}
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  color: '#06b6d4',
                  background: 'rgba(6, 182, 212, 0.1)',
                  border: '1px solid rgba(6, 182, 212, 0.3)',
                  borderRadius: '5px',
                  padding: '0.2rem 0.55rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                Sync with Live Campus Air
              </button>
            )}
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '1.25rem',
            }}
          >
            {/* Dry-Bulb Temperature Slider */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                <span style={{ color: '#94a3b8' }}>Dry-Bulb Temp (T_db):</span>
                <strong style={{ color: '#f59e0b', fontFamily: 'monospace' }}>{sliderTemp}°C</strong>
              </div>
              <input
                id="psychro-temp-slider"
                type="range"
                min="0"
                max="50"
                step="0.5"
                value={sliderTemp}
                onChange={(e) => onTempChange(parseFloat(e.target.value))}
                style={{ width: '100%', cursor: 'pointer' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#64748b' }}>
                <span>0°C</span>
                <span>25°C</span>
                <span>50°C</span>
              </div>
            </div>

            {/* Relative Humidity Slider */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                <span style={{ color: '#94a3b8' }}>Relative Humidity (RH):</span>
                <strong style={{ color: '#06b6d4', fontFamily: 'monospace' }}>{sliderRH}%</strong>
              </div>
              <input
                id="psychro-rh-slider"
                type="range"
                min="5"
                max="100"
                step="1"
                value={sliderRH}
                onChange={(e) => onRHChange(parseFloat(e.target.value))}
                style={{ width: '100%', cursor: 'pointer' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#64748b' }}>
                <span>5%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>
          </div>

          {/* Synchronized Live Psychrometric Output Badges */}
          {targetPoint && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
                gap: '0.5rem',
                background: '#090e1a',
                padding: '0.6rem 0.8rem',
                borderRadius: '8px',
                border: '1px solid rgba(255, 255, 255, 0.05)',
              }}
            >
              <div>
                <span style={{ fontSize: '0.68rem', color: '#64748b', display: 'block' }}>Humidity Ratio W</span>
                <strong style={{ fontSize: '0.9rem', color: '#f8fafc', fontFamily: 'monospace' }}>
                  {targetPoint.w} <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>g/kg</span>
                </strong>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: '#64748b', display: 'block' }}>Wet-Bulb T_wb</span>
                <strong style={{ fontSize: '0.9rem', color: '#06b6d4', fontFamily: 'monospace' }}>
                  {targetPoint.twb}°C
                </strong>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: '#64748b', display: 'block' }}>Dew Point T_dp</span>
                <strong style={{ fontSize: '0.9rem', color: '#38bdf8', fontFamily: 'monospace' }}>
                  {targetPoint.tdp}°C
                </strong>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: '#64748b', display: 'block' }}>Heat Index</span>
                <strong style={{ fontSize: '0.9rem', color: targetPoint.hiColor || '#ef4444', fontFamily: 'monospace' }}>
                  {targetPoint.hi}°C
                </strong>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: '#64748b', display: 'block' }}>ASHRAE 55 Status</span>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    padding: '0.15rem 0.45rem',
                    borderRadius: '4px',
                    display: 'inline-block',
                    backgroundColor: targetPoint.inComfort ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.15)',
                    color: targetPoint.inComfort ? '#10b981' : '#f87171',
                    border: `1px solid ${targetPoint.inComfort ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.3)'}`,
                  }}
                >
                  {targetPoint.inComfort ? 'Comfortable' : 'Outside Envelope'}
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Primary SVG Chart */}
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

          {/* Constant Wet-Bulb Guide Line passing through active point */}
          {guideLine && (
            <line
              x1={guideLine.x1}
              y1={guideLine.y1}
              x2={guideLine.x2}
              y2={guideLine.y2}
              stroke="rgba(236, 72, 153, 0.45)"
              strokeWidth="1.2"
              strokeDasharray="3 3"
            />
          )}

          {/* Active Operating Point (Synchronized with slider values) */}
          {targetPoint && (
            <g>
              {/* Orthogonal projection guides to axes */}
              <line
                x1={scaleX(targetPoint.t)}
                y1={scaleY(targetPoint.w)}
                x2={scaleX(targetPoint.t)}
                y2={padding.top + plotHeight}
                stroke="rgba(236, 72, 153, 0.5)"
                strokeDasharray="2 2"
              />
              <line
                x1={padding.left}
                y1={scaleY(targetPoint.w)}
                x2={scaleX(targetPoint.t)}
                y2={scaleY(targetPoint.w)}
                stroke="rgba(236, 72, 153, 0.5)"
                strokeDasharray="2 2"
              />

              {/* Pulsing indicator */}
              <circle
                cx={scaleX(targetPoint.t)}
                cy={scaleY(targetPoint.w)}
                r="14"
                fill="none"
                stroke="#ec4899"
                strokeWidth="1.5"
                opacity="0.6"
              >
                <animate attributeName="r" values="7;18;7" dur="2s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.8;0;0.8" dur="2s" repeatCount="indefinite" />
              </circle>
              {/* Core solid marker */}
              <circle
                cx={scaleX(targetPoint.t)}
                cy={scaleY(targetPoint.w)}
                r="7"
                fill="#ec4899"
                stroke="#ffffff"
                strokeWidth="2"
              />

              {/* Point coordinate tooltip tag */}
              <g transform={`translate(${Math.min(plotWidth + 10, scaleX(targetPoint.t) + 10)}, ${Math.max(padding.top + 15, scaleY(targetPoint.w) - 10)})`}>
                <rect
                  x="0"
                  y="-14"
                  width="92"
                  height="26"
                  rx="4"
                  fill="rgba(10, 15, 29, 0.88)"
                  stroke="#ec4899"
                  strokeWidth="1"
                />
                <text
                  x="6"
                  y="2"
                  fill="#f8fafc"
                  fontSize="9.5"
                  fontWeight="600"
                  fontFamily="monospace"
                >
                  {targetPoint.t}°C, {targetPoint.w}g/kg
                </text>
              </g>
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
        <div
          style={{
            display: 'flex',
            gap: '1.2rem',
            justifyContent: 'center',
            marginTop: '0.6rem',
            fontSize: '0.8rem',
            color: '#94a3b8',
            flexWrap: 'wrap',
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: 12, height: 2, background: '#06b6d4' }}></span> 100% Saturation
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span
              style={{
                width: 10,
                height: 10,
                background: 'rgba(16, 185, 129, 0.3)',
                border: '1px solid #10b981',
              }}
            ></span>{' '}
            ASHRAE 55 Comfort
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ec4899' }}></span> Operating State
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: 12, height: 1, borderTop: '2px dashed rgba(236, 72, 153, 0.6)' }}></span> Constant Wet-Bulb Line
          </span>
        </div>
      </div>
    </div>
  );
}
