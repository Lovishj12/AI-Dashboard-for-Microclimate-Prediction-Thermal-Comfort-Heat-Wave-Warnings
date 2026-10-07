"""
Scientific Calculation Engine for Microclimate & Thermal Comfort.
Implements rigorously documented, validated thermodynamic and biometeorological algorithms:
1. Saturation Vapor Pressure (e_s) & Actual Vapor Pressure (e_a) [Sonntag 1990 / Tetens]
2. Dew Point Temperature (T_dp) [Magnus-Tetens formulation, WMO standard]
3. Wet-Bulb Temperature (T_wb) [Stull (2011) empirical formula]
4. Humidity Ratio (W) [ASHRAE Handbook of Fundamentals, Dalton's Law]
5. Specific Enthalpy of Moist Air (h) [ASHRAE formulation]
6. NOAA/NWS Rothfusz Heat Index (HI) with Steadman low/high humidity corrections
7. Australian BoM Simplified Wet-Bulb Globe Temperature (sWBGT)
8. Environmental and Thermal Stress Category Classifications
"""

import numpy as np
import pandas as pd
from typing import Union, Tuple

Numeric = Union[float, np.ndarray, pd.Series]

# Standard Sea-Level Atmospheric Pressure (hPa)
STANDARD_PRESSURE_HPA = 1013.25

def saturation_vapor_pressure(temperature_c: Numeric) -> Numeric:
    """
    Calculate saturation vapor pressure e_s(T) over liquid water in hPa.
    Formula: Magnus-Tetens form (Sonntag 1990 / Buck 1981):
        e_s(T) = 6.112 * exp((17.67 * T) / (T + 243.5))
    Valid range: -40°C to +50°C.
    """
    return 6.112 * np.exp((17.67 * temperature_c) / (temperature_c + 243.5))

def actual_vapor_pressure(temperature_c: Numeric, relative_humidity_pct: Numeric) -> Numeric:
    """
    Calculate actual partial vapor pressure e_a in hPa.
    Formula:
        e_a = (RH / 100) * e_s(T)
    """
    e_s = saturation_vapor_pressure(temperature_c)
    return (relative_humidity_pct / 100.0) * e_s

def dew_point_temperature(temperature_c: Numeric, relative_humidity_pct: Numeric) -> Numeric:
    """
    Calculate dew point temperature T_dp in °C using the inverted Magnus-Tetens formula.
    
    Formula:
        alpha = ((17.67 * T) / (T + 243.5)) + ln(RH / 100)
        T_dp = (243.5 * alpha) / (17.67 - alpha)
        
    Source: Sonntag (1990), WMO Guide to Meteorological Instruments.
    Accuracy: ±0.1°C over range 0°C to 50°C.
    """
    rh_clipped = np.clip(relative_humidity_pct, 1e-4, 100.0)
    alpha = ((17.67 * temperature_c) / (temperature_c + 243.5)) + np.log(rh_clipped / 100.0)
    t_dp = (243.5 * alpha) / (17.67 - alpha)
    return t_dp

def wet_bulb_temperature(temperature_c: Numeric, relative_humidity_pct: Numeric) -> Numeric:
    """
    Calculate wet-bulb temperature T_wb in °C using Stull's empirical equation.
    
    Formula:
        T_wb = T * atan(0.151977 * sqrt(RH + 8.313659))
             + atan(T + RH) - atan(RH - 1.676331)
             + 0.00391838 * (RH^(3/2)) * atan(0.023101 * RH)
             - 4.686035
             
    Source: Stull, R. (2011). "Wet-Bulb Temperature from Relative Humidity and Air Temperature".
            Journal of Applied Meteorology and Climatology, 50(11), 2267-2269.
    Valid range: RH from 5% to 99%, T from -20°C to 50°C (standard pressure).
    Mean absolute error: ~0.16°C.
    """
    T = temperature_c
    RH = relative_humidity_pct
    
    t_wb = (
        T * np.arctan(0.151977 * np.sqrt(RH + 8.313659))
        + np.arctan(T + RH)
        - np.arctan(RH - 1.676331)
        + 0.00391838 * np.power(RH, 1.5) * np.arctan(0.023101 * RH)
        - 4.686035
    )
    return t_wb

def humidity_ratio(
    dew_point_c: Numeric,
    surface_pressure_hpa: Numeric = STANDARD_PRESSURE_HPA
) -> Numeric:
    """
    Calculate humidity ratio W (mass of water vapor per unit mass of dry air, kg_w / kg_da).
    
    Formula:
        e_a = saturation_vapor_pressure(T_dp)
        W = 0.62198 * e_a / (P_atm - e_a)
        
    Source: ASHRAE Handbook of Fundamentals (Psychrometric principles, Dalton's Law).
    """
    e_a = saturation_vapor_pressure(dew_point_c)
    w = 0.62198 * e_a / (surface_pressure_hpa - e_a)
    return np.maximum(w, 0.0)

def specific_enthalpy(temperature_c: Numeric, humidity_ratio_kg_kg: Numeric) -> Numeric:
    """
    Calculate specific enthalpy of moist air h in kJ / kg of dry air.
    
    Formula:
        h = c_pa * T + W * (h_we + c_pw * T)
        h = 1.006 * T + W * (2501.0 + 1.86 * T)
        
    Source: ASHRAE Handbook of Fundamentals.
    Units:
        T: °C
        W: kg water / kg dry air
        h: kJ / kg dry air
    """
    return 1.006 * temperature_c + humidity_ratio_kg_kg * (2501.0 + 1.86 * temperature_c)

def heat_index(temperature_c: Numeric, relative_humidity_pct: Numeric) -> Numeric:
    """
    Calculate NOAA/NWS Heat Index (HI) in °C using the Rothfusz regression equation
    with Steadman's low/high humidity corrections.
    
    Source: National Weather Service (NWS) Technical Attachment (SR 90-23) by Rothfusz (1990).
    Input: T in °C, RH in %.
    Output: Heat Index in °C.
    """
    # Convert T to Fahrenheit for NWS Rothfusz polynomial
    T_f = temperature_c * 9.0 / 5.0 + 32.0
    RH = relative_humidity_pct
    
    # Steadman simple formula
    HI_simple_f = 0.5 * (T_f + 61.0 + ((T_f - 68.0) * 1.2) + (RH * 0.094))
    
    # Full Rothfusz regression equation (applied when (HI_simple + T_f) / 2 >= 80°F)
    HI_full_f = (
        -42.379
        + 2.04901523 * T_f
        + 10.14333127 * RH
        - 0.22475541 * T_f * RH
        - 0.00683783 * T_f * T_f
        - 0.05481717 * RH * RH
        + 0.00122874 * T_f * T_f * RH
        + 0.00085282 * T_f * RH * RH
        - 0.00000199 * T_f * T_f * RH * RH
    )
    
    # Adjustment 1: Low humidity adjustment (RH < 13% and 80 <= T_f <= 112)
    adj_low = ((13.0 - RH) / 4.0) * np.sqrt(np.maximum(0.0, (17.0 - np.abs(T_f - 95.0)) / 17.0))
    # Adjustment 2: High humidity adjustment (RH > 85% and 80 <= T_f <= 87)
    adj_high = ((RH - 85.0) / 10.0) * ((87.0 - T_f) / 5.0)
    
    # Apply conditions element-wise or scalar
    is_series = isinstance(T_f, (pd.Series, np.ndarray))
    
    if is_series:
        hi_result_f = np.where(
            (HI_simple_f + T_f) / 2.0 < 80.0,
            HI_simple_f,
            HI_full_f
        )
        
        # Apply low RH adjustment
        cond_low = (RH < 13.0) & (T_f >= 80.0) & (T_f <= 112.0)
        hi_result_f = np.where(cond_low, hi_result_f - adj_low, hi_result_f)
        
        # Apply high RH adjustment
        cond_high = (RH > 85.0) & (T_f >= 80.0) & (T_f <= 87.0)
        hi_result_f = np.where(cond_high, hi_result_f + adj_high, hi_result_f)
    else:
        if (HI_simple_f + T_f) / 2.0 < 80.0:
            hi_result_f = HI_simple_f
        else:
            hi_result_f = HI_full_f
            if RH < 13.0 and 80.0 <= T_f <= 112.0:
                hi_result_f -= adj_low
            elif RH > 85.0 and 80.0 <= T_f <= 87.0:
                hi_result_f += adj_high

    # Convert back to Celsius: C = (F - 32) * 5 / 9
    hi_c = (hi_result_f - 32.0) * 5.0 / 9.0
    return hi_c

def simplified_wbgt(
    temperature_c: Numeric,
    relative_humidity_pct: Numeric
) -> Numeric:
    """
    Calculate Simplified Wet-Bulb Globe Temperature (sWBGT) in °C.
    Formula derived by Australian Bureau of Meteorology (BoM):
        sWBGT = 0.567 * T_db + 0.393 * e_a + 3.94
    where:
        T_db = dry-bulb temperature in °C
        e_a  = water vapor pressure in hPa
        
    Source: Australian Bureau of Meteorology (BoM) Heat Index & sWBGT Bulletin.
    Assumes moderate solar radiation and typical air movement.
    """
    e_a = actual_vapor_pressure(temperature_c, relative_humidity_pct)
    return 0.567 * temperature_c + 0.393 * e_a + 3.94

def classify_heat_index(hi_c: float) -> Tuple[str, str]:
    """
    Return NOAA/NWS Heat Index Alert Category and Color Code.
    """
    if hi_c < 27.0:
        return "Normal", "#2ecc71"
    elif hi_c < 32.0:
        return "Caution", "#f1c40f"
    elif hi_c < 39.0:
        return "Extreme Caution", "#e67e22"
    elif hi_c < 51.0:
        return "Danger", "#e74c3c"
    else:
        return "Extreme Danger", "#8e44ad"

def classify_wbgt(wbgt_c: float) -> Tuple[str, str]:
    """
    Return OSHA / ISO 7243 WBGT Occupational Risk Level.
    """
    if wbgt_c < 26.7:
        return "Low Risk", "#2ecc71"
    elif wbgt_c < 29.4:
        return "Moderate Risk", "#f1c40f"
    elif wbgt_c < 32.2:
        return "High Risk", "#e67e22"
    else:
        return "Extreme Risk", "#e74c3c"

def enrich_meteorological_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorized computation of all scientific metrics for an input DataFrame.
    Expects columns: 'temperature_c', 'relative_humidity_pct'.
    Optional column: 'surface_pressure_hpa' (defaults to 1013.25 if absent).
    
    Adds:
    - 'dew_point_c'
    - 'wet_bulb_c'
    - 'vapor_pressure_hpa'
    - 'humidity_ratio_kg_kg'
    - 'humidity_ratio_g_kg'
    - 'enthalpy_kj_kg'
    - 'heat_index_c'
    - 'swbgt_c'
    """
    out = df.copy()
    p_hpa = out["surface_pressure_hpa"] if "surface_pressure_hpa" in out.columns else STANDARD_PRESSURE_HPA
    
    t = out["temperature_c"]
    rh = out["relative_humidity_pct"]
    
    out["dew_point_c"] = dew_point_temperature(t, rh).round(2)
    out["wet_bulb_c"] = wet_bulb_temperature(t, rh).round(2)
    out["vapor_pressure_hpa"] = actual_vapor_pressure(t, rh).round(2)
    out["humidity_ratio_kg_kg"] = humidity_ratio(out["dew_point_c"], p_hpa).round(5)
    out["humidity_ratio_g_kg"] = (out["humidity_ratio_kg_kg"] * 1000.0).round(2)
    out["enthalpy_kj_kg"] = specific_enthalpy(t, out["humidity_ratio_kg_kg"]).round(2)
    out["heat_index_c"] = heat_index(t, rh).round(2)
    out["swbgt_c"] = simplified_wbgt(t, rh).round(2)
    
    return out
