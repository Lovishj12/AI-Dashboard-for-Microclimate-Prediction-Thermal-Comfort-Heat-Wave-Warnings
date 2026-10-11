/**
 * Rigorous Thermodynamic & Psychrometric Calculations in JavaScript.
 * Directly mirrors `src/scientific_engine.py` (Sonntag, Magnus-Tetens, Stull 2011,
 * ASHRAE Fundamentals, and NOAA Rothfusz equations).
 * Sea-level standard atmospheric pressure P_atm = 1013.25 hPa.
 */

export const STANDARD_PRESSURE_HPA = 1013.25;

/**
 * Saturation vapor pressure e_s(T) in hPa (Magnus-Tetens formula: Sonntag 1990).
 * Valid range: -40°C to +50°C.
 */
export function saturationVaporPressure(tempC) {
  return 6.112 * Math.exp((17.67 * tempC) / (tempC + 243.5));
}

/**
 * Actual vapor pressure e_a in hPa.
 */
export function actualVaporPressure(tempC, rhPct) {
  const es = saturationVaporPressure(tempC);
  return (rhPct / 100.0) * es;
}

/**
 * Dew point temperature T_dp in °C using inverted Magnus-Tetens formula.
 */
export function dewPointTemperature(tempC, rhPct) {
  const rhClipped = Math.max(1e-4, Math.min(100.0, rhPct));
  const alpha = ((17.67 * tempC) / (tempC + 243.5)) + Math.log(rhClipped / 100.0);
  return (243.5 * alpha) / (17.67 - alpha);
}

/**
 * Wet-bulb temperature T_wb in °C using Stull (2011) empirical equation.
 * Valid range: RH from 5% to 99%, T from -20°C to 50°C.
 */
export function wetBulbTemperature(tempC, rhPct) {
  const T = tempC;
  const RH = rhPct;
  const twb =
    T * Math.atan(0.151977 * Math.sqrt(RH + 8.313659)) +
    Math.atan(T + RH) -
    Math.atan(RH - 1.676331) +
    0.00391838 * Math.pow(RH, 1.5) * Math.atan(0.023101 * RH) -
    4.686035;
  return twb;
}

/**
 * Humidity ratio W in g water vapor per kg dry air (g/kg).
 * Uses Dalton's Law: W = 0.62198 * e_a / (P_atm - e_a) * 1000.
 */
export function humidityRatioGPerKg(dewPointC, pressureHpa = STANDARD_PRESSURE_HPA) {
  const ea = saturationVaporPressure(dewPointC);
  const w = (0.62198 * ea) / (pressureHpa - ea);
  return Math.max(0, w * 1000.0);
}

/**
 * Specific enthalpy of moist air h in kJ/kg dry air (ASHRAE Handbook of Fundamentals).
 * h = 1.006 * T + (W_kg) * (2501.0 + 1.86 * T)
 */
export function specificEnthalpy(tempC, wGPerKg) {
  const wKg = wGPerKg / 1000.0;
  return 1.006 * tempC + wKg * (2501.0 + 1.86 * tempC);
}

/**
 * NOAA/NWS Rothfusz Heat Index in °C with Steadman adjustments.
 */
export function calculateHeatIndex(tempC, rhPct) {
  const Tf = tempC * (9.0 / 5.0) + 32.0;
  const RH = rhPct;

  const hiSimpleF = 0.5 * (Tf + 61.0 + (Tf - 68.0) * 1.2 + RH * 0.094);

  let hiF =
    -42.379 +
    2.04901523 * Tf +
    10.14333127 * RH -
    0.22475541 * Tf * RH -
    0.00683783 * Tf * Tf -
    0.05481717 * RH * RH +
    0.00122874 * Tf * Tf * RH +
    0.00085282 * Tf * RH * RH -
    0.00000199 * Tf * Tf * RH * RH;

  if ((hiSimpleF + Tf) / 2.0 < 80.0) {
    hiF = hiSimpleF;
  } else {
    if (RH < 13.0 && Tf >= 80.0 && Tf <= 112.0) {
      const adjLow = ((13.0 - RH) / 4.0) * Math.sqrt(Math.max(0, (17.0 - Math.abs(Tf - 95.0)) / 17.0));
      hiF -= adjLow;
    } else if (RH > 85.0 && Tf >= 80.0 && Tf <= 87.0) {
      const adjHigh = ((RH - 85.0) / 10.0) * ((87.0 - Tf) / 5.0);
      hiF += adjHigh;
    }
  }

  return (hiF - 32.0) * (5.0 / 9.0);
}

/**
 * Simplified Wet-Bulb Globe Temperature (sWBGT) in °C (Australian BoM).
 * sWBGT = 0.567 * T_db + 0.393 * e_a + 3.94
 */
export function calculateSwbgt(tempC, rhPct) {
  const ea = actualVaporPressure(tempC, rhPct);
  return 0.567 * tempC + 0.393 * ea + 3.94;
}

/**
 * Classifies NOAA Heat Index into alert level and hex color.
 */
export function classifyHeatIndex(hiC) {
  if (hiC < 27.0) return { level: 'Normal', color: '#10b981' };
  if (hiC < 32.0) return { level: 'Caution', color: '#eab308' };
  if (hiC < 39.0) return { level: 'Extreme Caution', color: '#f97316' };
  if (hiC < 51.0) return { level: 'Danger', color: '#ef4444' };
  return { level: 'Extreme Danger', color: '#a855f7' };
}

/**
 * Checks whether a given state point (T_db, W_g_kg) falls inside
 * the ASHRAE Standard 55 summer comfort polygon.
 */
export function isInsideAshraeComfort(tempC, wGPerKg) {
  // Polygon vertices: (23.5, 4.5), (27.5, 5.0), (28.5, 12.0), (24.5, 12.0)
  const polygon = [
    [23.5, 4.5],
    [27.5, 5.0],
    [28.5, 12.0],
    [24.5, 12.0],
  ];

  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i][0];
    const yi = polygon[i][1];
    const xj = polygon[j][0];
    const yj = polygon[j][1];

    const intersect =
      yi > wGPerKg !== yj > wGPerKg &&
      tempC < ((xj - xi) * (wGPerKg - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

/**
 * High-performance full thermodynamic state calculation for any (T_db, RH).
 */
export function computeAirState(tempC, rhPct, pressureHpa = STANDARD_PRESSURE_HPA) {
  const t = Number(tempC);
  const rh = Number(rhPct);

  const tdp = dewPointTemperature(t, rh);
  const twb = wetBulbTemperature(t, rh);
  const w = humidityRatioGPerKg(tdp, pressureHpa);
  const h = specificEnthalpy(t, w);
  const hi = calculateHeatIndex(t, rh);
  const swbgt = calculateSwbgt(t, rh);
  const { level: hiLevel, color: hiColor } = classifyHeatIndex(hi);
  const inComfort = isInsideAshraeComfort(t, w);

  return {
    t: Number(t.toFixed(1)),
    rh: Number(rh.toFixed(1)),
    w: Number(w.toFixed(2)),
    tdp: Number(tdp.toFixed(1)),
    twb: Number(twb.toFixed(1)),
    h: Number(h.toFixed(1)),
    hi: Number(hi.toFixed(1)),
    swbgt: Number(swbgt.toFixed(1)),
    hiLevel,
    hiColor,
    inComfort,
  };
}
