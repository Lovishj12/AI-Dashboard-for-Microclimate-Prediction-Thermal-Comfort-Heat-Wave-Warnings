import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Polygon, Polyline, Popup, Tooltip, useMap } from 'react-leaflet';
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
      let coords = selectedBuilding.geometry.coordinates;
      if (selectedBuilding.geometry.type === 'Polygon') {
        coords = coords[0];
      }
      if (Array.isArray(coords) && coords.length > 0) {
        const latlngs = coords.map(([lng, lat]) => [lat, lng]);
        const bounds = L.latLngBounds(latlngs);
        map.flyToBounds(bounds, { padding: [60, 60], maxZoom: 17, duration: 1.2 });
      }
    }
  }, [selectedBuilding, map]);

  return null;
}

/**
 * Continuous thermal color map generator (Turbo / Thermal Jet spectrum).
 * Maps normalized scalar t in [0, 1] to smooth RGB color string.
 * Cooler: Deep Blue -> Cyan -> Emerald Green -> Yellow -> Orange -> Vivid Red (Hotter)
 */
function getContinuousThermalColor(val, minVal, maxVal) {
  if (val === null || val === undefined || isNaN(val)) return '#64748b';
  const t = Math.max(0.0, Math.min(1.0, (val - minVal) / (maxVal - minVal || 1.0)));

  // 6-step scientific thermal palette keypoints
  const stops = [
    { pos: 0.0, r: 30, g: 58, b: 138 },    // 0.0: Deep Navy / Cool Blue (#1e3a8a)
    { pos: 0.2, r: 6, g: 182, b: 212 },    // 0.2: Bright Cyan (#06b6d4)
    { pos: 0.4, r: 16, g: 185, b: 129 },   // 0.4: Emerald Green (#10b981)
    { pos: 0.6, r: 234, g: 179, b: 8 },    // 0.6: Golden Yellow (#eab308)
    { pos: 0.8, r: 249, g: 115, b: 22 },   // 0.8: Deep Amber / Orange (#f97316)
    { pos: 1.0, r: 225, g: 29, b: 72 },    // 1.0: Vivid Hot Thermal Red (#e11d48)
  ];

  let lower = stops[0];
  let upper = stops[stops.length - 1];
  for (let i = 0; i < stops.length - 1; i++) {
    if (t >= stops[i].pos && t <= stops[i + 1].pos) {
      lower = stops[i];
      upper = stops[i + 1];
      break;
    }
  }

  const range = upper.pos - lower.pos || 1;
  const ratio = (t - lower.pos) / range;
  const r = Math.round(lower.r + (upper.r - lower.r) * ratio);
  const g = Math.round(lower.g + (upper.g - lower.g) * ratio);
  const b = Math.round(lower.b + (upper.b - lower.b) * ratio);

  return `rgb(${r}, ${g}, ${b})`;
}

export default function CampusMap({ selectedBuildingId, onSelectBuilding, mode = 'ai' }) {
  const [geoData, setGeoData] = useState(null);
  const [microclimateData, setMicroclimateData] = useState(null);

  // Layer modes: 'surface_temp', 'air_temp', 'thermal_comfort', 'temp_delta', 'vulnerability', 'category'
  const [layerMode, setLayerMode] = useState('surface_temp');
  const [forecastHorizon, setForecastHorizon] = useState('current'); // 'current', '1', '3', '6', '24'

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Default IIT KGP Campus Centroid & Zoom
  const campusCenter = [22.3175, 87.3085];
  const defaultZoom = 15;

  // Fetch campus building spatial data and current downscaled microclimate
  useEffect(() => {
    async function fetchCampusData() {
      try {
        setLoading(true);
        const [geoRes, microRes] = await Promise.all([
          fetch('http://127.0.0.1:8000/api/campus/buildings'),
          fetch(`http://127.0.0.1:8000/api/campus/microclimate/current?mode=${mode}`),
        ]);

        if (!geoRes.ok) throw new Error(`GeoJSON fetch failed: HTTP ${geoRes.status}`);
        if (!microRes.ok) throw new Error(`Microclimate fetch failed: HTTP ${microRes.status}`);

        const geo = await geoRes.json();
        const micro = await microRes.json();

        setGeoData(geo);
        setMicroclimateData(micro);
      } catch (err) {
        console.error('Error fetching campus spatial data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchCampusData();
  }, [mode]);

  // Update microclimate data when forecast horizon changes
  useEffect(() => {
    async function fetchForecast() {
      try {
        const microUrl =
          forecastHorizon === 'current'
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
  }, [forecastHorizon]);

  // Compute active buildings dataset
  const activeBuildings = useMemo(() => {
    return microclimateData?.buildings || [];
  }, [microclimateData]);

  // Map building ID to its active microclimate state
  const microclimateMap = useMemo(() => {
    const map = {};
    activeBuildings.forEach((b) => {
      map[b.id] = b;
    });
    return map;
  }, [activeBuildings]);

  // Active layer metadata (title, units, range, and provenance disclosure)
  const layerMeta = useMemo(() => {
    switch (layerMode) {
      case 'surface_temp':
        return {
          title: 'Surface Temperature (Rooftop / Skin LST)',
          units: '°C',
          min: 24.0,
          max: 42.0,
          source: 'Calculated Surface Energy Balance (Albedo × Solar Radiation / Convective Attenuation)',
          resolution: 'Building Footprint Scale (10-30m)',
          status: 'Calculated Thermal State',
          note: 'Shows estimated skin/rooftop surface temperature, which can exceed air temperature on dark surfaces.',
        };
      case 'air_temp':
        return {
          title: 'Air Temperature (Dry-Bulb T_db)',
          units: '°C',
          min: 22.0,
          max: 38.0,
          source: 'Regional Synoptic Station + UNSW Microclimate Canopy Downscaling',
          resolution: 'Precinct Scale (30m buffer)',
          status: 'Physics-Downscaled Observation / Estimate',
          note: 'Ambient air temperature at 2m height experienced by humans.',
        };
      case 'thermal_comfort':
        return {
          title: 'Thermal Comfort (NOAA Heat Index)',
          units: '°C',
          min: 24.0,
          max: 45.0,
          source: 'Rothfusz Equation + Biometeorological Vapor Pressure Coupling',
          resolution: 'Precinct Scale (30m buffer)',
          status: 'Biometeorological Index',
          note: 'Apparent temperature combining local ambient air and evaporative relative humidity.',
        };
      case 'temp_delta':
        return {
          title: 'Urban Heat Island Anomaly (ΔT vs Regional Baseline)',
          units: '°C',
          min: -2.0,
          max: 3.5,
          source: 'Surface Albedo, Imperviousness, Tree Canopy, and SVF Perturbation Matrix',
          resolution: 'Precinct Scale',
          status: 'Modelled Perturbation Anomaly',
          note: 'Thermal departure relative to regional reference station (Cooling islands vs hotspots).',
        };
      case 'vulnerability':
        return {
          title: 'Heat Vulnerability Index (HVI)',
          units: 'pts (0-100)',
          min: 15.0,
          max: 85.0,
          source: 'Hazard Exposure (40%) + AC Deficit (35%) + Footfall Density (25%)',
          resolution: 'Precinct Scale',
          status: 'Synthesized Vulnerability Score',
          note: 'Ranks physical risk and demographic non-AC heat vulnerability.',
        };
      case 'ac_heat_rejection':
        return {
          title: 'AC Outdoor Heat Rejection (Q_reject = Q_cooling + P_electric)',
          units: 'kW',
          min: 0.0,
          max: 1500.0,
          source: 'Thermodynamic Energy Balance & IIT Kharagpur e-Procurement / HMC Policy Database',
          resolution: 'Building Footprint Scale',
          status: 'Documented & Benchmarked HVAC Engineering Model',
          note: 'Total sensible and latent heat rejected into outdoor air by air-conditioning condenser banks.',
        };
      case 'category':
      default:
        return {
          title: 'Campus Land-Use Typology',
          units: 'Category',
          min: 0,
          max: 0,
          source: 'IIT Kharagpur Campus Directory & OpenStreetMap Zoning',
          resolution: 'Categorical Polygon',
          status: 'Land-Use Classification',
          note: 'Functional zoning of academic, residential, sports, and natural water bodies.',
        };
    }
  }, [layerMode]);

  // Color ramp resolver for a building feature
  const getFeatureColor = (feature) => {
    const bId = feature.properties.id;
    const bObj = microclimateMap[bId];
    const micro = bObj?.microclimate;
    const ac = bObj?.ac_inventory;
    const cat = feature.properties.category;

    if (layerMode === 'category') {
      if (cat === 'Hostel') return '#8b5cf6';
      if (cat === 'Sports' || cat === 'Sports/Open') return '#10b981';
      if (cat === 'Commercial' || cat === 'Hospital' || cat === 'Healthcare') return '#f59e0b';
      if (cat === 'Water Body' || cat === 'Water/Nature') return '#06b6d4';
      if (cat === 'Roads/Corridor') return '#f97316';
      return '#3b82f6'; // Academic
    }

    if (layerMode === 'ac_heat_rejection') {
      const q = ac ? ac.heat_rejection_kw : 0.0;
      return getContinuousThermalColor(q, layerMeta.min, layerMeta.max);
    }

    if (layerMode === 'surface_temp') {
      const st = micro ? (micro.surface_temperature_c || micro.temperature_c + 2.5) : 30.0;
      return getContinuousThermalColor(st, layerMeta.min, layerMeta.max);
    }

    if (layerMode === 'air_temp') {
      const t = micro ? micro.temperature_c : 28.0;
      return getContinuousThermalColor(t, layerMeta.min, layerMeta.max);
    }

    if (layerMode === 'thermal_comfort') {
      const hi = micro ? micro.heat_index_c : 32.0;
      return getContinuousThermalColor(hi, layerMeta.min, layerMeta.max);
    }

    if (layerMode === 'temp_delta') {
      const dt = micro ? micro.temperature_delta_c : 0.0;
      return getContinuousThermalColor(dt, layerMeta.min, layerMeta.max);
    }

    if (layerMode === 'vulnerability') {
      const v = micro ? micro.vulnerability_score : 45.0;
      return getContinuousThermalColor(v, layerMeta.min, layerMeta.max);
    }

    return '#3b82f6';
  };

  const getPolygonStyle = (feature) => {
    const isSelected = selectedBuildingId === feature.properties.id;
    const fillColor = getFeatureColor(feature);

    return {
      fillColor: fillColor,
      fillOpacity: isSelected ? 0.92 : 0.75,
      color: isSelected ? '#ffffff' : 'rgba(255, 255, 255, 0.45)',
      weight: isSelected ? 3.5 : 1.2,
      dashArray: isSelected ? '' : '',
    };
  };

  const selectedBuilding = geoData?.features?.find(
    (f) => f.properties.id === selectedBuildingId
  );

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', position: 'relative' }}>
      {/* Top Header & Layer Mode Selector */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1rem',
          flexWrap: 'wrap',
          gap: '0.8rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <h3 style={{ fontSize: '1.18rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
              Building-Level Microclimate Thermal Heatmap
            </h3>
            <span
              style={{
                fontSize: '0.68rem',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '10px',
                background: 'rgba(6, 182, 212, 0.15)',
                color: '#06b6d4',
                border: '1px solid rgba(6, 182, 212, 0.3)',
              }}
            >
              HIGH-RESOLUTION GIS
            </span>
          </div>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.2rem' }}>
            IIT Kharagpur Campus Core (2,100 Acres) • Georeferenced Rooftops, Road Corridors & Canopy Downscaling
          </p>
        </div>

        {/* Thematic Layer & AI Forecast Horizon Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', flexWrap: 'wrap' }}>
          {/* AI Forecast Horizon Selector */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem',
              background: 'rgba(255,255,255,0.03)',
              padding: '0.25rem 0.4rem',
              borderRadius: '8px',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, marginRight: '0.2rem' }}>
              Forecast Horizon:
            </span>
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

          {/* 5-Category Selectable Thermal Layer Switcher */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              background: 'rgba(255,255,255,0.03)',
              padding: '0.3rem 0.5rem',
              borderRadius: '8px',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>Thermal Layer:</span>
            <select
              value={layerMode}
              onChange={(e) => setLayerMode(e.target.value)}
              style={{
                background: '#0a0f1d',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.4)',
                borderRadius: '6px',
                padding: '0.25rem 0.6rem',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="surface_temp">Surface Temperature (Rooftop / LST °C)</option>
              <option value="air_temp">Air Temperature (Dry-Bulb T_db °C)</option>
              <option value="thermal_comfort">Thermal Comfort (NOAA Heat Index °C)</option>
              <option value="temp_delta">UHI Microclimate Anomaly (ΔT °C)</option>
              <option value="vulnerability">Heat Vulnerability Index (0-100)</option>
              <option value="ac_heat_rejection">AC Outdoor Heat Rejection (Q_reject kW)</option>
              <option value="category">Campus Land-Use Typology</option>
            </select>
          </div>
        </div>
      </div>

      {/* Dynamic Scientific Thermal Gradient Legend Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.8rem',
          background: 'rgba(15, 23, 42, 0.85)',
          padding: '0.5rem 0.9rem',
          borderRadius: '8px',
          fontSize: '0.75rem',
          flexWrap: 'wrap',
          gap: '0.6rem',
          border: '1px solid rgba(255, 255, 255, 0.06)',
        }}
      >
        <div style={{ color: '#94a3b8' }}>
          Active View: <strong style={{ color: '#f8fafc' }}>{layerMeta.title}</strong>
          <span style={{ fontSize: '0.7rem', color: '#64748b', marginLeft: '0.6rem' }}>
            Focus: High-Resolution Campus Buildings ({geoData?.features?.length || 24} Precincts)
          </span>
        </div>

        {/* Continuous Color Gradient Bar */}
        {layerMode !== 'category' ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '0.72rem', color: '#38bdf8', fontWeight: 600 }}>
              {layerMeta.min} {layerMeta.units} (Cooler)
            </span>
            <div
              style={{
                width: '160px',
                height: '10px',
                borderRadius: '5px',
                background: 'linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #eab308, #f97316, #e11d48)',
                boxShadow: '0 0 8px rgba(0,0,0,0.5)',
                border: '1px solid rgba(255,255,255,0.2)',
              }}
            ></div>
            <span style={{ fontSize: '0.72rem', color: '#e11d48', fontWeight: 600 }}>
              {layerMeta.max} {layerMeta.units} (Hotter)
            </span>
          </div>
        ) : (
          <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              <span style={{ width: 10, height: 10, background: '#3b82f6', borderRadius: '2px' }}></span> Academic
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              <span style={{ width: 10, height: 10, background: '#8b5cf6', borderRadius: '2px' }}></span> Hostel
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              <span style={{ width: 10, height: 10, background: '#10b981', borderRadius: '2px' }}></span> Sports/Open
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              <span style={{ width: 10, height: 10, background: '#06b6d4', borderRadius: '2px' }}></span> Water Body
            </span>
          </div>
        )}
      </div>

      {/* Selected Building Active Thermal Alert Signal Floating HUD */}
      {selectedBuilding && microclimateMap[selectedBuilding.properties.id] && (() => {
        const selMicro = microclimateMap[selectedBuilding.properties.id].microclimate;
        const riskLabel = selMicro?.risk_status?.[0] || selMicro?.heat_index_risk || 'Normal';
        const riskColor = selMicro?.risk_status?.[1] || (
          riskLabel === 'Danger' ? '#ef4444' :
          riskLabel === 'Extreme Caution' ? '#f97316' :
          riskLabel === 'Caution' ? '#f59e0b' : '#10b981'
        );

        return (
          <div
            className="alert-pulse-badge"
            style={{
              marginBottom: '0.75rem',
              padding: '0.65rem 1rem',
              borderRadius: '8px',
              background: `linear-gradient(90deg, rgba(15, 23, 42, 0.95), ${riskColor}28)`,
              border: `1.5px solid ${riskColor}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.8rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span
                className="beacon-dot"
                style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  background: riskColor,
                  boxShadow: `0 0 10px ${riskColor}`,
                  display: 'inline-block',
                }}
              ></span>
              <div>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  ACTIVE BUILDING ALERT SIGNAL
                </span>
                <div style={{ fontSize: '0.92rem', fontWeight: 800, color: '#f8fafc' }}>
                  {selectedBuilding.properties.name} — <span style={{ color: riskColor }}>{riskLabel.toUpperCase()}</span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1.2rem', alignItems: 'center', fontSize: '0.78rem' }}>
              <div>
                <span style={{ color: '#94a3b8' }}>Heat Index: </span>
                <strong style={{ color: riskColor, fontSize: '0.92rem' }}>{selMicro.heat_index_c}°C</strong>
              </div>
              <div>
                <span style={{ color: '#94a3b8' }}>Wet-Bulb: </span>
                <strong style={{ color: selMicro.wet_bulb_c >= 30 ? '#ef4444' : '#38bdf8' }}>{selMicro.wet_bulb_c}°C</strong>
              </div>
              <div>
                <span style={{ color: '#94a3b8' }}>Rooftop LST: </span>
                <strong style={{ color: '#f97316' }}>{selMicro.surface_temperature_c || (selMicro.temperature_c + 2.5).toFixed(1)}°C</strong>
              </div>
            </div>
          </div>
        );
      })()}

      {loading && (
        <div style={{ height: '520px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#06b6d4' }}>
          <span>Loading IIT Kharagpur spatial microclimate layers...</span>
        </div>
      )}

      {error && (
        <div style={{ height: '520px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444' }}>
          <span>Error loading campus map: {error}</span>
        </div>
      )}

      {!loading && !error && geoData && (
        <div style={{ height: '520px', borderRadius: '10px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.08)' }}>
          <MapContainer
            center={campusCenter}
            zoom={defaultZoom}
            minZoom={14}
            maxZoom={18}
            scrollWheelZoom={true}
            style={{ height: '100%', width: '100%', background: '#0a0f1d' }}
          >
            {/* OpenStreetMap Basemap (Free, Open-Source, 0 API Keys required, Dark Filter applied via CSS) */}
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              maxZoom={19}
            />

            <CampusViewportHandler selectedBuilding={selectedBuilding} />

            {/* Primary Campus Landmark Precincts with Physics Downscaling */}
            {geoData.features.map((feature) => {
              const coords = feature.geometry.coordinates[0];
              const latlngs = coords.map(([lng, lat]) => [lat, lng]);
              const props = feature.properties;
              const micro = microclimateMap[props.id]?.microclimate;
              const isSelected = selectedBuildingId === props.id;

              const riskLabel = micro?.risk_status?.[0] || micro?.heat_index_risk || 'Normal';
              const riskColor = micro?.risk_status?.[1] || (
                riskLabel === 'Danger' ? '#ef4444' :
                riskLabel === 'Extreme Caution' ? '#f97316' :
                riskLabel === 'Caution' ? '#f59e0b' : '#10b981'
              );

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
                        {layerMode === 'surface_temp' && micro
                          ? `Rooftop LST: ${micro.surface_temperature_c || (micro.temperature_c + 2.5).toFixed(1)}°C`
                          : layerMode === 'air_temp' && micro
                          ? `Air Temp (T_db): ${micro.temperature_c}°C`
                          : layerMode === 'thermal_comfort' && micro
                          ? `Heat Index: ${micro.heat_index_c}°C`
                          : layerMode === 'temp_delta' && micro
                          ? `Delta: ${micro.temperature_delta_c > 0 ? '+' : ''}${micro.temperature_delta_c}°C`
                          : layerMode === 'vulnerability' && micro
                          ? `HVI: ${micro.vulnerability_score}/100`
                          : props.category}
                      </span>
                    </div>
                  </Tooltip>
                  <Popup>
                    <div style={{ color: '#0f172a', padding: '0.2rem', minWidth: '240px' }}>
                      {/* Active Alert Signal Header */}
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          marginBottom: '0.4rem',
                          paddingBottom: '0.35rem',
                          borderBottom: '1px solid #e2e8f0',
                        }}
                      >
                        <strong style={{ fontSize: '0.92rem', color: '#0f172a' }}>
                          {props.name}
                        </strong>
                        <span
                          style={{
                            fontSize: '0.68rem',
                            fontWeight: 800,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background: riskColor,
                            color: '#ffffff',
                          }}
                        >
                          ● {riskLabel.toUpperCase()}
                        </span>
                      </div>

                      <span style={{ fontSize: '0.74rem', color: '#64748b', display: 'block', marginBottom: '0.4rem' }}>
                        {props.category} • Footfall: {props.estimated_footfall}
                      </span>

                      {/* Prominent Alert Signal Banner */}
                      <div
                        style={{
                          background: riskLabel === 'Danger' || riskLabel === 'Extreme Caution' ? '#fef2f2' : '#f0fdf4',
                          border: `1px solid ${riskColor}`,
                          borderRadius: '6px',
                          padding: '0.35rem 0.5rem',
                          marginBottom: '0.45rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.4rem',
                        }}
                      >
                        <span style={{ fontSize: '1rem' }}>
                          {riskLabel === 'Danger' ? '🚨' : riskLabel === 'Extreme Caution' ? '⚠️' : '⚡'}
                        </span>
                        <div style={{ fontSize: '0.72rem', color: '#1e293b', fontWeight: 600 }}>
                          Alert Signal: <span style={{ color: riskColor }}>{riskLabel} Alert</span>
                          <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 400 }}>
                            {riskLabel === 'Danger' ? 'Heat exhaustion likely. Reduce outdoor exposure.' :
                             riskLabel === 'Extreme Caution' ? 'Sunstroke possible with prolonged activity.' :
                             'Normal academic precinct operating condition.'}
                          </div>
                        </div>
                      </div>

                      {micro && (
                        <div
                          style={{
                            fontSize: '0.75rem',
                            lineHeight: '1.45',
                            background: '#f8fafc',
                            padding: '0.45rem',
                            borderRadius: '4px',
                            marginBottom: '0.45rem',
                            border: '1px solid #e2e8f0',
                          }}
                        >
                          <div>
                            <strong>Estimated Rooftop LST:</strong>{' '}
                            <span style={{ color: '#ea580c', fontWeight: 700 }}>
                              {micro.surface_temperature_c || (micro.temperature_c + 2.5).toFixed(1)}°C
                            </span>
                          </div>
                          <div>
                            <strong>Modelled Air Temp:</strong> {micro.temperature_c}°C (
                            {micro.temperature_delta_c > 0 ? '+' : ''}
                            {micro.temperature_delta_c}°C)
                          </div>
                          <div>
                            <strong>Heat Index:</strong> {micro.heat_index_c}°C ({micro.heat_index_risk})
                          </div>
                          <div>
                            <strong>Wet-Bulb:</strong> {micro.wet_bulb_c}°C
                          </div>
                          <div>
                            <strong>Vulnerability Score:</strong> {micro.vulnerability_score} / 100
                          </div>
                        </div>
                      )}
                      <button
                        onClick={() => onSelectBuilding && onSelectBuilding(props.id)}
                        style={{
                          width: '100%',
                          padding: '0.35rem 0.5rem',
                          background: isSelected ? '#0284c7' : '#06b6d4',
                          border: 'none',
                          borderRadius: '4px',
                          color: '#fff',
                          fontWeight: 600,
                          fontSize: '0.75rem',
                          cursor: 'pointer',
                        }}
                      >
                        {isSelected ? '✓ Selected in Inspector' : 'Inspect Precinct Details'}
                      </button>
                    </div>
                  </Popup>
                </Polygon>
              );
            })}
          </MapContainer>
        </div>
      )}

      {/* Layer Scientific Attribution Note */}
      <div
        style={{
          marginTop: '0.6rem',
          padding: '0.4rem 0.8rem',
          borderRadius: '6px',
          background: 'rgba(255, 255, 255, 0.02)',
          fontSize: '0.72rem',
          color: '#64748b',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.4rem',
        }}
      >
        <span>
          ℹ️ <strong style={{ color: '#94a3b8' }}>Scientific Disclosure:</strong> {layerMeta.note} Data source: {layerMeta.source}.
        </span>
        <span style={{ color: '#38bdf8' }}>Timezone: Asia/Kolkata (IST)</span>
      </div>

      {/* Quick Landmark Navigate Buttons Bar */}
      {geoData && (
        <div style={{ marginTop: '0.7rem', display: 'flex', gap: '0.4rem', overflowX: 'auto', paddingBottom: '0.3rem' }}>
          <span style={{ fontSize: '0.75rem', color: '#64748b', alignSelf: 'center', whiteSpace: 'nowrap', marginRight: '0.2rem' }}>
            Quick Navigate:
          </span>
          {geoData.features.slice(0, 10).map((f) => (
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
