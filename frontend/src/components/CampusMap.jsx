import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polygon, Popup, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';

// Fix default Leaflet icon paths in bundler environments
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Component to dynamically fit campus bounds or fly to selection
function CampusViewportHandler({ selectedBuilding }) {
  const map = useMap();

  useEffect(() => {
    if (selectedBuilding && selectedBuilding.geometry) {
      const coords = selectedBuilding.geometry.coordinates[0];
      const latlngs = coords.map(([lng, lat]) => [lat, lng]);
      const bounds = L.latLngBounds(latlngs);
      map.flyToBounds(bounds, { padding: [60, 60], maxZoom: 17, duration: 1.2 });
    }
  }, [selectedBuilding, map]);

  return null;
}

export default function CampusMap({ selectedBuildingId, onSelectBuilding }) {
  const [geoData, setGeoData] = useState(null);
  const [microclimateData, setMicroclimateData] = useState(null);
  const [layerMode, setLayerMode] = useState('heat_index'); // 'category', 'heat_index', 'wet_bulb', 'temp_delta', 'vulnerability'
  const [forecastHorizon, setForecastHorizon] = useState('current'); // 'current', '1', '3', '6', '24'
  
  // 24-Hour Diurnal Time Animation State
  const [diurnalTimeline, setDiurnalTimeline] = useState(null);
  const [diurnalHour, setDiurnalHour] = useState(14); // Default to peak afternoon 14:00
  const [isPlayingDiurnal, setIsPlayingDiurnal] = useState(false);
  const [useDiurnalMode, setUseDiurnalMode] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Default IIT KGP Campus Centroid & Zoom
  const campusCenter = [22.3160, 87.3080];
  const defaultZoom = 15;

  // Fetch initial campus spatial data and diurnal simulation dataset
  useEffect(() => {
    async function fetchCampusData() {
      try {
        setLoading(true);
        const [geoRes, microRes, diurnalRes] = await Promise.all([
          fetch('http://127.0.0.1:8000/api/campus/buildings'),
          fetch('http://127.0.0.1:8000/api/campus/microclimate/current'),
          fetch('http://127.0.0.1:8000/api/campus/diurnal'),
        ]);

        if (!geoRes.ok) throw new Error(`GeoJSON fetch failed: HTTP ${geoRes.status}`);
        if (!microRes.ok) throw new Error(`Microclimate fetch failed: HTTP ${microRes.status}`);
        if (!diurnalRes.ok) throw new Error(`Diurnal fetch failed: HTTP ${diurnalRes.status}`);

        const geo = await geoRes.json();
        const micro = await microRes.json();
        const diurnal = await diurnalRes.json();

        setGeoData(geo);
        setMicroclimateData(micro);
        setDiurnalTimeline(diurnal);
      } catch (err) {
        console.error('Error fetching campus spatial data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchCampusData();
  }, []);

  // Update microclimate data when horizon changes (if not in diurnal mode)
  useEffect(() => {
    if (useDiurnalMode) return;
    async function fetchForecast() {
      try {
        const microUrl = forecastHorizon === 'current'
          ? 'http://127.0.0.1:8000/api/campus/microclimate/current'
          : `http://127.0.0.1:8000/api/campus/forecast/${forecastHorizon}`;
        const res = await fetch(microUrl);
        if (res.ok) {
          const data = await res.json();
          setMicroclimateData(data);
        }
      } catch (err) {
        console.error('Forecast fetch error:', err);
      }
    }
    fetchForecast();
  }, [forecastHorizon, useDiurnalMode]);

  // Handle Diurnal Time Slider Playback Animation
  useEffect(() => {
    let timer;
    if (isPlayingDiurnal && useDiurnalMode) {
      timer = setInterval(() => {
        setDiurnalHour((prev) => (prev + 1) % 24);
      }, 1000); // Step 1 hour every second
    }
    return () => clearInterval(timer);
  }, [isPlayingDiurnal, useDiurnalMode]);

  // Compute active buildings dataset depending on mode
  const activeBuildings = React.useMemo(() => {
    if (useDiurnalMode && diurnalTimeline && diurnalTimeline[diurnalHour]) {
      return diurnalTimeline[diurnalHour].buildings;
    }
    return microclimateData?.buildings || [];
  }, [useDiurnalMode, diurnalTimeline, diurnalHour, microclimateData]);

  // Map building ID to its active microclimate state
  const microclimateMap = React.useMemo(() => {
    const map = {};
    activeBuildings.forEach((b) => {
      map[b.id] = b;
    });
    return map;
  }, [activeBuildings]);

  // Color ramp generators for different thematic heat layers
  const getFeatureColor = (feature) => {
    const bId = feature.properties.id;
    const micro = microclimateMap[bId]?.microclimate;
    const cat = feature.properties.category;

    if (layerMode === 'category') {
      if (cat === 'Hostel') return '#8b5cf6';
      if (cat === 'Sports' || cat === 'Sports/Open') return '#10b981';
      if (cat === 'Commercial' || cat === 'Hospital' || cat === 'Healthcare') return '#f59e0b';
      if (cat === 'Water Body' || cat === 'Water/Nature') return '#06b6d4';
      if (cat === 'Roads/Corridor') return '#ef4444';
      return '#3b82f6'; // Academic
    }

    if (layerMode === 'heat_index') {
      const hi = micro ? micro.heat_index_c : 34.0;
      if (hi < 27.0) return '#10b981'; // Safe
      if (hi < 32.0) return '#3b82f6'; // Caution
      if (hi < 39.0) return '#f59e0b'; // Extreme Caution
      if (hi < 45.0) return '#ef4444'; // Danger
      return '#881337'; // Extreme Danger
    }

    if (layerMode === 'wet_bulb') {
      const twb = micro ? micro.wet_bulb_c : 27.0;
      if (twb < 26.0) return '#10b981';
      if (twb < 28.0) return '#06b6d4';
      if (twb < 30.0) return '#f59e0b';
      if (twb < 32.0) return '#ef4444';
      return '#881337'; // Lethal threshold approaching
    }

    if (layerMode === 'temp_delta') {
      const dt = micro ? micro.temperature_delta_c : 0.0;
      if (dt <= -1.0) return '#06b6d4'; // Strong cooling island
      if (dt < 0.0) return '#10b981';  // Mild cooling island
      if (dt < 0.8) return '#f59e0b';  // Mild UHI
      return '#ef4444';                // Strong UHI hotspot
    }

    if (layerMode === 'vulnerability') {
      const v = micro ? micro.vulnerability_score : 50.0;
      if (v < 40.0) return '#10b981'; // Low Vulnerability
      if (v < 60.0) return '#f59e0b'; // Medium Vulnerability
      if (v < 75.0) return '#f97316'; // High Vulnerability
      return '#ef4444';               // Extreme Vulnerability
    }

    return '#3b82f6';
  };

  const getPolygonStyle = (feature) => {
    const isSelected = selectedBuildingId === feature.properties.id;
    const fillColor = getFeatureColor(feature);

    return {
      fillColor: fillColor,
      fillOpacity: isSelected ? 0.85 : 0.60,
      color: isSelected ? '#ffffff' : '#94a3b8',
      weight: isSelected ? 3.5 : 1.2,
      dashArray: isSelected ? '' : '2, 2',
    };
  };

  const selectedBuilding = geoData?.features?.find(
    (f) => f.properties.id === selectedBuildingId
  );

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', position: 'relative' }}>
      {/* Top Header & Layer Mode Selector */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.8rem' }}>
        <div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            Interactive Campus Spatial Microclimate & Heatmap
          </h3>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.2rem' }}>
            IIT Kharagpur Campus Core (2,100 Acres) • 24 Verified Landmark Polygons
          </p>
        </div>

        {/* Thematic Layer & AI Forecast Horizon Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', flexWrap: 'wrap' }}>
          {/* Mode Switcher: AI Forecast vs Diurnal Animation */}
          <div style={{ display: 'flex', gap: '0.3rem', background: 'rgba(255,255,255,0.03)', padding: '0.2rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <button
              onClick={() => { setUseDiurnalMode(false); setIsPlayingDiurnal(false); }}
              style={{
                fontSize: '0.72rem',
                fontWeight: 600,
                padding: '0.25rem 0.6rem',
                borderRadius: '6px',
                background: !useDiurnalMode ? '#06b6d4' : 'transparent',
                color: !useDiurnalMode ? '#0a0f1d' : '#94a3b8',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              AI Forecasts
            </button>
            <button
              onClick={() => { setUseDiurnalMode(true); }}
              style={{
                fontSize: '0.72rem',
                fontWeight: 600,
                padding: '0.25rem 0.6rem',
                borderRadius: '6px',
                background: useDiurnalMode ? '#ec4899' : 'transparent',
                color: useDiurnalMode ? '#ffffff' : '#94a3b8',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              24h Diurnal Animation
            </button>
          </div>

          {/* AI Horizon Selector (When not in diurnal mode) */}
          {!useDiurnalMode && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', background: 'rgba(255,255,255,0.03)', padding: '0.25rem 0.4rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, marginRight: '0.2rem' }}>Timeline:</span>
              {[
                { id: 'current', label: 'Now' },
                { id: '1', label: '+1h' },
                { id: '3', label: '+3h' },
                { id: '6', label: '+6h' },
                { id: '24', label: '+24h' },
              ].map((h) => (
                <button
                  key={h.id}
                  onClick={() => setForecastHorizon(h.id)}
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    padding: '0.2rem 0.5rem',
                    borderRadius: '5px',
                    background: forecastHorizon === h.id ? '#06b6d4' : 'transparent',
                    color: forecastHorizon === h.id ? '#0a0f1d' : '#94a3b8',
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {h.label}
                </button>
              ))}
            </div>
          )}

          {/* 24-Hour Diurnal Playback Controls (When in diurnal mode) */}
          {useDiurnalMode && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', background: 'rgba(236, 72, 153, 0.1)', padding: '0.25rem 0.6rem', borderRadius: '8px', border: '1px solid rgba(236, 72, 153, 0.3)' }}>
              <button
                onClick={() => setIsPlayingDiurnal(!isPlayingDiurnal)}
                style={{
                  background: '#ec4899',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '0.2rem 0.6rem',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                {isPlayingDiurnal ? '⏸ Pause' : '▶ Play 24h'}
              </button>
              <input
                type="range"
                min="0"
                max="23"
                value={diurnalHour}
                onChange={(e) => setDiurnalHour(parseInt(e.target.value))}
                style={{ width: '100px', cursor: 'pointer' }}
              />
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f8fafc', minWidth: '45px' }}>
                {diurnalHour.toString().padStart(2, '0')}:00
              </span>
            </div>
          )}

          {/* Layer Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(255,255,255,0.03)', padding: '0.3rem 0.5rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>Layer:</span>
            <select
              value={layerMode}
              onChange={(e) => setLayerMode(e.target.value)}
              style={{
                background: '#0a0f1d',
                color: '#06b6d4',
                border: '1px solid rgba(6, 182, 212, 0.4)',
                borderRadius: '6px',
                padding: '0.25rem 0.6rem',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="heat_index">NOAA Heat Index (°C)</option>
              <option value="wet_bulb">Stull Wet-Bulb (°C)</option>
              <option value="temp_delta">Microclimate Delta ΔT (°C)</option>
              <option value="vulnerability">Heat Vulnerability Index (0-100)</option>
              <option value="category">Landmark Category</option>
            </select>
          </div>
        </div>
      </div>

      {/* Layer Context & Active Legend Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem', background: 'rgba(255,255,255,0.02)', padding: '0.4rem 0.8rem', borderRadius: '6px', fontSize: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ color: '#94a3b8' }}>
          Active View: <strong style={{ color: '#f8fafc' }}>{
            layerMode === 'heat_index' ? 'NOAA Apparent Heat Risk' :
            layerMode === 'wet_bulb' ? 'Stull Evaporative Limit (Twb)' :
            layerMode === 'temp_delta' ? 'Urban Heat Island (UHI) Perturbation' :
            layerMode === 'vulnerability' ? 'Exposure & AC-Deficit Vulnerability' : 'Land-Use Precinct Typology'
          }</strong>
        </div>

        {/* Dynamic Legend */}
        <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center' }}>
          {layerMode === 'heat_index' && (
            <>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#10b981', borderRadius: '2px' }}></span> &lt;27° Safe</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#3b82f6', borderRadius: '2px' }}></span> 27-32° Caution</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#f59e0b', borderRadius: '2px' }}></span> 32-39° Ext. Caution</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#ef4444', borderRadius: '2px' }}></span> 39-45° Danger</span>
            </>
          )}

          {layerMode === 'wet_bulb' && (
            <>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#10b981', borderRadius: '2px' }}></span> &lt;26° Optimal</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#06b6d4', borderRadius: '2px' }}></span> 26-28° Moderate</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#f59e0b', borderRadius: '2px' }}></span> 28-30° Elevated</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#ef4444', borderRadius: '2px' }}></span> &ge;30° Critical Limit</span>
            </>
          )}

          {layerMode === 'temp_delta' && (
            <>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#06b6d4', borderRadius: '2px' }}></span> &le; -1.0° Cooling Island</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#10b981', borderRadius: '2px' }}></span> -1° to 0° Mild Cooling</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#f59e0b', borderRadius: '2px' }}></span> 0° to +0.8° Moderate UHI</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#ef4444', borderRadius: '2px' }}></span> &gt; +0.8° Severe Hotspot</span>
            </>
          )}

          {layerMode === 'vulnerability' && (
            <>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#10b981', borderRadius: '2px' }}></span> &lt;40 Low</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#f59e0b', borderRadius: '2px' }}></span> 40-60 Moderate</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#f97316', borderRadius: '2px' }}></span> 60-75 High</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#ef4444', borderRadius: '2px' }}></span> &gt;75 Extreme</span>
            </>
          )}

          {layerMode === 'category' && (
            <>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#3b82f6', borderRadius: '2px' }}></span> Academic</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#8b5cf6', borderRadius: '2px' }}></span> Hostel</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#10b981', borderRadius: '2px' }}></span> Sports/Open</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}><span style={{ width: 10, height: 10, background: '#06b6d4', borderRadius: '2px' }}></span> Water Body</span>
            </>
          )}
        </div>
      </div>

      {loading && (
        <div style={{ height: '480px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#06b6d4' }}>
          <span>Loading IIT Kharagpur spatial microclimate layers...</span>
        </div>
      )}

      {error && (
        <div style={{ height: '480px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444' }}>
          <span>Error loading campus map: {error}</span>
        </div>
      )}

      {!loading && !error && geoData && (
        <div style={{ height: '480px', borderRadius: '10px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.08)' }}>
          <MapContainer
            center={campusCenter}
            zoom={defaultZoom}
            minZoom={14}
            maxZoom={18}
            scrollWheelZoom={true}
            style={{ height: '100%', width: '100%', background: '#0a0f1d' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <CampusViewportHandler selectedBuilding={selectedBuilding} />

            {geoData.features.map((feature) => {
              const coords = feature.geometry.coordinates[0];
              const latlngs = coords.map(([lng, lat]) => [lat, lng]);
              const props = feature.properties;
              const micro = microclimateMap[props.id]?.microclimate;
              const isSelected = selectedBuildingId === props.id;

              return (
                <Polygon
                  key={props.id}
                  positions={latlngs}
                  pathOptions={getPolygonStyle(feature)}
                  eventHandlers={{
                    click: () => {
                      if (onSelectBuilding) onSelectBuilding(props.id);
                    },
                  }}
                >
                  <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                      {props.name} <br />
                      <span style={{ color: '#06b6d4' }}>
                        {layerMode === 'heat_index' && micro ? `Heat Index: ${micro.heat_index_c}°C` :
                         layerMode === 'wet_bulb' && micro ? `Wet-Bulb: ${micro.wet_bulb_c}°C` :
                         layerMode === 'temp_delta' && micro ? `Delta: ${micro.temperature_delta_c > 0 ? '+' : ''}${micro.temperature_delta_c}°C` :
                         layerMode === 'vulnerability' && micro ? `HVI: ${micro.vulnerability_score}/100` :
                         props.category}
                      </span>
                    </div>
                  </Tooltip>
                  <Popup>
                    <div style={{ color: '#0f172a', padding: '0.2rem', minWidth: '200px' }}>
                      <strong style={{ fontSize: '0.9rem', color: '#0f172a', display: 'block' }}>{props.name}</strong>
                      <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block', marginBottom: '0.4rem' }}>
                        {props.category} • Footfall: {props.estimated_footfall}
                      </span>
                      {micro && (
                        <div style={{ fontSize: '0.75rem', lineHeight: '1.4', background: '#f8fafc', padding: '0.4rem', borderRadius: '4px', marginBottom: '0.4rem' }}>
                          <div><strong>Modelled T_db:</strong> {micro.temperature_c}°C ({micro.temperature_delta_c > 0 ? '+' : ''}{micro.temperature_delta_c}°C)</div>
                          <div><strong>Heat Index:</strong> {micro.heat_index_c}°C ({micro.heat_index_risk})</div>
                          <div><strong>Wet-Bulb:</strong> {micro.wet_bulb_c}°C</div>
                          <div><strong>Vulnerability:</strong> {micro.vulnerability_score} / 100</div>
                        </div>
                      )}
                      <button
                        onClick={() => onSelectBuilding && onSelectBuilding(props.id)}
                        style={{
                          width: '100%',
                          padding: '0.35rem 0.5rem',
                          background: '#06b6d4',
                          border: 'none',
                          borderRadius: '4px',
                          color: '#fff',
                          fontWeight: 600,
                          fontSize: '0.75rem',
                          cursor: 'pointer',
                        }}
                      >
                        {isSelected ? '✓ Selected in Inspector' : 'Inspect Building'}
                      </button>
                    </div>
                  </Popup>
                </Polygon>
              );
            })}
          </MapContainer>
        </div>
      )}

      {/* Quick Landmark Quick-Select Bar */}
      {geoData && (
        <div style={{ marginTop: '0.85rem', display: 'flex', gap: '0.4rem', overflowX: 'auto', paddingBottom: '0.4rem' }}>
          <span style={{ fontSize: '0.75rem', color: '#64748b', alignSelf: 'center', whiteSpace: 'nowrap', marginRight: '0.2rem' }}>
            Quick Navigate:
          </span>
          {geoData.features.slice(0, 8).map((f) => (
            <button
              key={f.properties.id}
              onClick={() => onSelectBuilding && onSelectBuilding(f.properties.id)}
              style={{
                fontSize: '0.72rem',
                padding: '0.25rem 0.6rem',
                background: selectedBuildingId === f.properties.id ? 'rgba(6, 182, 212, 0.25)' : 'rgba(255,255,255,0.04)',
                border: selectedBuildingId === f.properties.id ? '1px solid #06b6d4' : '1px solid rgba(255,255,255,0.08)',
                borderRadius: '6px',
                color: selectedBuildingId === f.properties.id ? '#06b6d4' : '#94a3b8',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.2s',
              }}
            >
              {f.properties.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
