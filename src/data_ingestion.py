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

if __name__ == "__main__":
    config = load_config()
    for loc in config["locations"]:
        ingest_location(loc)
