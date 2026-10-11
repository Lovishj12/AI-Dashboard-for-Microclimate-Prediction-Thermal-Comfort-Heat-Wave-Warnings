"""
NASA POWER Hourly Data Ingestion Module.
Downloads, validates, and archives hourly meteorological time-series for configured locations.
"""

import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from src.config import load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def fetch_nasa_power_hourly(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    parameters: list[str],
    community: str = "SB",
    base_url: str = "https://power.larc.nasa.gov/api/temporal/hourly/point"
) -> Dict[str, Any]:
    """
    Fetch hourly point meteorological data from NASA POWER API.
    
    Parameters:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        start_date: Format YYYYMMDD
        end_date: Format YYYYMMDD
        parameters: List of NASA POWER parameter codes (e.g. ['T2M', 'RH2M'])
        community: User community ('SB' for Sustainable Buildings, 'RE', 'AG')
    """
    param_str = ",".join(parameters)
    url = (
        f"{base_url}?parameters={param_str}&community={community}"
        f"&longitude={longitude:.4f}&latitude={latitude:.4f}"
        f"&start={start_date}&end={end_date}&format=JSON"
    )
    logger.info(f"Querying NASA POWER API: {url}")
    
    req = urllib.request.Request(url, headers={"User-Agent": "BTP-Microclimate-Research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status != 200:
                raise RuntimeError(f"NASA POWER API returned HTTP status {response.status}")
            data = json.loads(response.read().decode("utf-8"))
            return data
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        raise
    except urllib.error.URLError as e:
        logger.error(f"Network / URL Error: {e.reason}")
        raise

def parse_nasa_power_json(raw_json: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert raw NASA POWER JSON response into a clean pandas DataFrame with DatetimeIndex.
    """
    props = raw_json.get("properties", {})
    parameter_data = props.get("parameter", {})
    
    if not parameter_data:
        raise ValueError("NASA POWER response contains no parameter data.")
    
    df_dict = {}
    for param_name, time_series in parameter_data.items():
        df_dict[param_name] = time_series
        
    df = pd.DataFrame(df_dict)
    # NASA POWER hourly timestamps are in format: YYYYMMDDHH (e.g., '2023050100')
    df.index = pd.to_datetime(df.index, format="%Y%m%d%H")
    df.index.name = "timestamp_utc"
    
    # NASA missing value sentinel is -999.0
    df = df.replace(-999.0, pd.NA)
    
    # Convert pressure from kPa to hPa (1 kPa = 10 hPa) for standard meteorological calculations
    if "PS" in df.columns:
        df["surface_pressure_hpa"] = df["PS"] * 10.0
    
    # Rename standard variables to clean, self-describing scientific names
    rename_map = {
        "T2M": "temperature_c",
        "RH2M": "relative_humidity_pct",
        "WS2M": "wind_speed_ms",
        "ALLSKY_SFC_SW_DWN": "solar_radiation_wm2"
    }
    df = df.rename(columns=rename_map)
    return df

def ingest_location(
    location_key: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    force_download: bool = False
) -> Path:
    """
    Download and save raw JSON and processed Parquet/CSV for a given location.
    """
    config = load_config()
    loc_info = config["locations"].get(location_key)
    if not loc_info:
        raise KeyError(f"Location '{location_key}' not found in configuration.")
        
    pipeline_cfg = config["data_pipeline"]
    start_date = start_date or pipeline_cfg["default_start_date"]
    end_date = end_date or pipeline_cfg["default_end_date"]
    
    raw_dir = Path(pipeline_cfg["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_json_path = raw_dir / f"{location_key}_{start_date}_{end_date}.json"
    
    if raw_json_path.exists() and not force_download:
        logger.info(f"Raw cache hit: {raw_json_path}")
        with open(raw_json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    else:
        logger.info(f"Downloading data for {loc_info['name']} ({start_date} to {end_date})...")
        raw_data = fetch_nasa_power_hourly(
            latitude=loc_info["latitude"],
            longitude=loc_info["longitude"],
            start_date=start_date,
            end_date=end_date,
            parameters=pipeline_cfg["parameters"],
            community=pipeline_cfg.get("community", "SB")
        )
        with open(raw_json_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f)
        logger.info(f"Saved raw response to {raw_json_path}")
        
    # Parse and save cleaned raw tabular format
    df = parse_nasa_power_json(raw_data)
    df["location"] = location_key
    df["latitude"] = loc_info["latitude"]
    df["longitude"] = loc_info["longitude"]
    
    processed_dir = Path(pipeline_cfg["processed_dir"])
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    parquet_path = processed_dir / f"{location_key}_hourly.parquet"
    csv_path = processed_dir / f"{location_key}_hourly.csv"
    
    try:
        df.to_parquet(parquet_path)
        logger.info(f"Saved processed time series (parquet): {parquet_path}")
    except Exception as e:
        logger.warning(f"Parquet engine not available ({e}), saving CSV.")
    
    df.to_csv(csv_path)
    logger.info(f"Saved processed time series (CSV): {csv_path} ({len(df)} records)")
    return csv_path

# In-memory cache for recent telemetry to prevent repeated external API requests
_RECENT_TELEMETRY_CACHE = {}

def fetch_recent_telemetry_series(
    location_key: str = "kharagpur",
    hours: int = 72,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Fetches real-time / recent continuous hourly observations for IIT Kharagpur in Asia/Kolkata timezone.
    
    1. Attempts live query to Open-Meteo High-Resolution reanalysis/nowcast grid for IIT Kharagpur (22.3149°N, 87.3105°E).
    2. Enriches the hourly data with full physical and biometeorological parameters (Dew Point, Wet-Bulb, Heat Index, sWBGT).
    3. Trims to exact requested window (e.g., 72 continuous hours) up to the latest available observation.
    4. If network is unreachable or live feed fails, falls back to the archived NASA POWER baseline dataset and clearly
       flags the payload with data_source: "historical_benchmark".
    """
    import time
    from datetime import datetime
    import zoneinfo
    from src.scientific_engine import enrich_meteorological_dataframe

    config = load_config()
    loc_info = config["locations"].get(location_key)
    if not loc_info:
        raise KeyError(f"Location '{location_key}' not found in configuration.")

    cache_key = f"{location_key}_{hours}"
    now_ts = time.time()
    
    # Cache for 15 minutes (900 seconds)
    if not force_refresh and cache_key in _RECENT_TELEMETRY_CACHE:
        cached_entry = _RECENT_TELEMETRY_CACHE[cache_key]
        if now_ts - cached_entry["cached_at"] < 900:
            return cached_entry["data"]

    lat = loc_info["latitude"]
    lon = loc_info["longitude"]
    days_to_fetch = max(4, (hours // 24) + 2)

    # 1. Attempt live telemetry fetch
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat:.4f}&longitude={lon:.4f}"
            f"&hourly=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,direct_normal_irradiance"
            f"&past_days={days_to_fetch}&forecast_days=1&timezone=Asia%2FKolkata"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "BTP-IIT-Kharagpur-Research/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status == 200:
                raw_json = json.loads(resp.read().decode("utf-8"))
                hourly = raw_json.get("hourly", {})
                time_strings = hourly.get("time", [])

                if time_strings:
                    raw_df = pd.DataFrame({
                        "timestamp": pd.to_datetime(time_strings),
                        "temperature_c": hourly.get("temperature_2m", []),
                        "relative_humidity_pct": hourly.get("relative_humidity_2m", []),
                        "surface_pressure_hpa": hourly.get("surface_pressure", [1013.25] * len(time_strings)),
                        "wind_speed_ms": [round(w / 3.6, 2) for w in hourly.get("wind_speed_10m", [0.0] * len(time_strings))],
                        "solar_radiation_wm2": hourly.get("direct_normal_irradiance", [0.0] * len(time_strings))
                    })
                    raw_df.set_index("timestamp", inplace=True)
                    
                    # Fill any minor missing points with forward fill
                    raw_df = raw_df.ffill().bfill()
                    
                    # Compute thermodynamic & biometeorological variables
                    enriched_df = enrich_meteorological_dataframe(raw_df)

                    # Limit observations to up to current hour in Asia/Kolkata
                    tz_kolkata = zoneinfo.ZoneInfo("Asia/Kolkata")
                    now_ist = datetime.now(tz_kolkata)
                    current_hour_str = now_ist.strftime("%Y-%m-%d %H:00:00")
                    
                    obs_df = enriched_df[enriched_df.index <= current_hour_str]
                    if len(obs_df) < hours:
                        obs_df = enriched_df  # Fallback to full available slice

                    slice_df = obs_df.iloc[-hours:].copy()

                    records = []
                    for ts, row in slice_df.iterrows():
                        # ISO 8601 string with Asia/Kolkata timezone offset (+05:30)
                        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
                        records.append({
                            "timestamp": ts_str,
                            "iso_timestamp": f"{ts.strftime('%Y-%m-%dT%H:%M:%S')}+05:30",
                            "temperature_c": round(float(row["temperature_c"]), 1),
                            "relative_humidity_pct": round(float(row["relative_humidity_pct"]), 1),
                            "wet_bulb_c": round(float(row["wet_bulb_c"]), 1),
                            "dew_point_c": round(float(row["dew_point_c"]), 1),
                            "heat_index_c": round(float(row["heat_index_c"]), 1),
                            "swbgt_c": round(float(row["swbgt_c"]), 1),
                            "solar_radiation_wm2": round(float(row.get("solar_radiation_wm2", 0.0)), 1),
                            "wind_speed_ms": round(float(row.get("wind_speed_ms", 0.0)), 1)
                        })

                    result_data = {
                        "station_id": location_key,
                        "location_name": loc_info["name"],
                        "data_source": "live_telemetry",
                        "data_source_label": "Live Telemetry (Open-Meteo / IMD Grid)",
                        "timezone": "Asia/Kolkata",
                        "timezone_offset": "+05:30",
                        "hours": len(records),
                        "start_timestamp": records[0]["timestamp"] if records else None,
                        "end_timestamp": records[-1]["timestamp"] if records else None,
                        "series": records
                    }

                    _RECENT_TELEMETRY_CACHE[cache_key] = {
                        "cached_at": now_ts,
                        "data": result_data
                    }
                    return result_data
    except Exception as e:
        logger.warning(f"Live telemetry fetch for {location_key} failed ({e}). Falling back to curated historical dataset.")

    # 2. Graceful Fallback: Curated NASA POWER / IMD Historical Dataset
    processed_dir = Path(config["data_pipeline"]["processed_dir"]) / "enriched"
    csv_path = processed_dir / f"{location_key}_enriched_hourly.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Enriched historical dataset missing at {csv_path}")

    hist_df = pd.read_csv(csv_path, index_col="timestamp_utc", parse_dates=True)
    slice_df = hist_df.iloc[-hours:].copy()

    records = []
    for ts, row in slice_df.iterrows():
        # Convert UTC timestamp to Asia/Kolkata (+05:30)
        ts_utc = ts.tz_localize("UTC") if ts.tzinfo is None else ts
        ts_ist = ts_utc.tz_convert("Asia/Kolkata")
        records.append({
            "timestamp": ts_ist.strftime("%Y-%m-%d %H:%M:%S"),
            "iso_timestamp": ts_ist.isoformat(),
            "temperature_c": round(float(row["temperature_c"]), 1),
            "relative_humidity_pct": round(float(row["relative_humidity_pct"]), 1),
            "wet_bulb_c": round(float(row["wet_bulb_c"]), 1),
            "dew_point_c": round(float(row["dew_point_c"]), 1),
            "heat_index_c": round(float(row["heat_index_c"]), 1),
            "swbgt_c": round(float(row["swbgt_c"]), 1),
            "solar_radiation_wm2": round(float(row.get("solar_radiation_wm2", 0.0)), 1),
            "wind_speed_ms": round(float(row.get("wind_speed_ms", 0.0)), 1)
        })

    return {
        "station_id": location_key,
        "location_name": loc_info["name"],
        "data_source": "historical_benchmark",
        "data_source_label": "Historical Baseline (NASA POWER / IMD Curated Benchmark)",
        "timezone": "Asia/Kolkata",
        "timezone_offset": "+05:30",
        "hours": len(records),
        "start_timestamp": records[0]["timestamp"] if records else None,
        "end_timestamp": records[-1]["timestamp"] if records else None,
        "series": records
    }

if __name__ == "__main__":
    config = load_config()
    for loc in config["locations"]:
        ingest_location(loc)

