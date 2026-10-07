import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"

DEFAULT_CONFIG = {
    "locations": {
        "new_delhi": {
            "name": "New Delhi (Safdarjung)",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "elevation_m": 216,
            "climate_zone": "Composite / Semi-arid (Extreme Dry Heat)",
            "imd_normal_max_t_may": 39.9,
            "imd_normal_max_t_june": 39.2
        },
        "kharagpur": {
            "name": "Kharagpur (IIT Campus / WB)",
            "latitude": 22.3149,
            "longitude": 87.3105,
            "elevation_m": 61,
            "climate_zone": "Tropical Wet & Dry (Humid Heat Stress)",
            "imd_normal_max_t_may": 37.1,
            "imd_normal_max_t_june": 35.4
        },
        "ahmedabad": {
            "name": "Ahmedabad",
            "latitude": 23.0225,
            "longitude": 72.5714,
            "elevation_m": 53,
            "climate_zone": "Hot Semi-Arid (Severe Heat Wave Zone)",
            "imd_normal_max_t_may": 41.6,
            "imd_normal_max_t_june": 38.7
        }
    },
    "data_pipeline": {
        "nasa_power_base_url": "https://power.larc.nasa.gov/api/temporal/hourly/point",
        "community": "SB",
        "parameters": [
            "T2M",               # Temperature at 2m (deg C)
            "RH2M",              # Relative Humidity at 2m (%)
            "WS2M",              # Wind Speed at 2m (m/s)
            "PS",                # Surface Pressure (kPa)
            "ALLSKY_SFC_SW_DWN"  # All Sky Surface Shortwave Downward Irradiance (W/m^2)
        ],
        "default_start_date": "20230101",
        "default_end_date": "20240630",
        "raw_dir": "data/raw",
        "processed_dir": "data/processed",
        "reports_dir": "reports/eda"
    },
    "warning_thresholds": {
        "imd": {
            "plains_base_t_max": 40.0,
            "heat_wave_departure_min": 4.5,
            "heat_wave_departure_severe": 6.4,
            "heat_wave_absolute_min": 45.0,
            "heat_wave_absolute_severe": 47.0
        },
        "heat_index": {
            "caution": 27.0,
            "extreme_caution": 32.0,
            "danger": 39.0,
            "extreme_danger": 51.0
        },
        "wbgt": {
            "low": 26.7,
            "moderate": 29.4,
            "high": 32.2
        },
        "wet_bulb": {
            "extreme_danger": 35.0,
            "severe_danger": 31.0
        }
    }
}

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return DEFAULT_CONFIG

def save_default_config():
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)

if __name__ == "__main__":
    save_default_config()
    print(f"Configuration written to {CONFIG_PATH}")
