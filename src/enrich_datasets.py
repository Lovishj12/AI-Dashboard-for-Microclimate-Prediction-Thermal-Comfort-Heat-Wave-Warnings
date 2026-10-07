"""
Batch Data Processor & Scientific Enrichment Pipeline.
Applies the validated scientific engine to all ingested hourly datasets,
generating enriched time series containing thermodynamic state variables
(dew point, wet-bulb, humidity ratio, enthalpy, heat index, sWBGT)
and saving enriched CSV datasets for subsequent ML and Visualization phases.
"""

from pathlib import Path
import pandas as pd
import logging

from src.config import load_config
from src.scientific_engine import enrich_meteorological_dataframe

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def process_and_enrich_all():
    config = load_config()
    processed_dir = Path(config["data_pipeline"]["processed_dir"])
    enriched_dir = processed_dir / "enriched"
    enriched_dir.mkdir(parents=True, exist_ok=True)
    
    locations = config["locations"]
    for loc_key in locations:
        raw_csv = processed_dir / f"{loc_key}_hourly.csv"
        if not raw_csv.exists():
            logger.warning(f"File {raw_csv} not found, skipping.")
            continue
            
        logger.info(f"Enriching time series for {loc_key}...")
        df = pd.read_csv(raw_csv, index_col="timestamp_utc", parse_dates=True)
        
        enriched_df = enrich_meteorological_dataframe(df)
        
        output_csv = enriched_dir / f"{loc_key}_enriched_hourly.csv"
        enriched_df.to_csv(output_csv)
        logger.info(f"Saved {output_csv} ({len(enriched_df)} rows, {len(enriched_df.columns)} columns)")
        
        # Display sample thermal summary
        max_hi = enriched_df["heat_index_c"].max()
        max_wb = enriched_df["wet_bulb_c"].max()
        max_swbgt = enriched_df["swbgt_c"].max()
        logger.info(f"[{loc_key.upper()}] Max HI: {max_hi:.1f}°C | Max Twb: {max_wb:.1f}°C | Max sWBGT: {max_swbgt:.1f}°C")

if __name__ == "__main__":
    process_and_enrich_all()
