"""
Exploratory Data Analysis (EDA) & Data Quality Pipeline.
Audits meteorological time series, computes descriptive statistics,
checks temporal continuity and missing values, identifies seasonal patterns,
and generates research summary reports and charts.
"""

from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from src.config import load_config

def run_eda_for_location(location_key: str, processed_csv_path: Path, output_dir: Path) -> dict:
    """
    Run exploratory data analysis on a processed hourly CSV dataset.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(processed_csv_path, index_col="timestamp_utc", parse_dates=True)
    
    # 1. Temporal Coverage & Continuity Check
    total_records = len(df)
    start_dt = df.index.min()
    end_dt = df.index.max()
    expected_hours = int((end_dt - start_dt).total_seconds() / 3600) + 1
    missing_timestamps = expected_hours - total_records
    
    # 2. Missing Value Analysis
    missing_per_col = df.isnull().sum().to_dict()
    
    # 3. Duplicate Records
    duplicate_count = df.index.duplicated().sum()
    
    # 4. Descriptive Statistics
    num_cols = ["temperature_c", "relative_humidity_pct", "wind_speed_ms", "surface_pressure_hpa", "solar_radiation_wm2"]
    stats_df = df[num_cols].describe().round(2)
    stats_dict = stats_df.to_dict()
    
    # 5. Correlation Matrix
    corr_matrix = df[num_cols].corr().round(3).to_dict()
    
    # 6. Extreme Heat Wave / Temperature Outlier Events
    heat_days_40c = (df["temperature_c"] >= 40.0).sum()
    heat_days_45c = (df["temperature_c"] >= 45.0).sum()
    max_temp = df["temperature_c"].max()
    min_temp = df["temperature_c"].min()
    
    # 7. Generate EDA Summary Plots
    fig, axes = plt.subplots(3, 2, figsize=(15, 12))
    fig.suptitle(f"Microclimate Exploratory Analysis: {location_key.upper()} (2023 - 2024)", fontsize=16, fontweight="bold")
    
    # 7a. Temperature Time Series
    axes[0, 0].plot(df.index, df["temperature_c"], color="#e74c3c", linewidth=0.6, alpha=0.8)
    axes[0, 0].axhline(40.0, color="orange", linestyle="--", label="IMD Plains Base (40°C)")
    axes[0, 0].axhline(45.0, color="red", linestyle="--", label="IMD Heat Wave (45°C)")
    axes[0, 0].set_title("Hourly Dry-Bulb Temperature (°C)")
    axes[0, 0].set_ylabel("°C")
    axes[0, 0].legend(loc="upper left")
    axes[0, 0].grid(True, alpha=0.3)
    
    # 7b. Relative Humidity Time Series
    axes[0, 1].plot(df.index, df["relative_humidity_pct"], color="#3498db", linewidth=0.6, alpha=0.8)
    axes[0, 1].set_title("Hourly Relative Humidity (%)")
    axes[0, 1].set_ylabel("%")
    axes[0, 1].grid(True, alpha=0.3)
    
    # 7c. Temperature vs Humidity Scatter (Heat Stress Phase Space)
    scatter = axes[1, 0].scatter(df["temperature_c"], df["relative_humidity_pct"], c=df["solar_radiation_wm2"], cmap="plasma", alpha=0.3, s=10)
    axes[1, 0].set_title("Temperature vs Relative Humidity (colored by Solar Radiation)")
    axes[1, 0].set_xlabel("Dry-Bulb Temp (°C)")
    axes[1, 0].set_ylabel("Relative Humidity (%)")
    axes[1, 0].grid(True, alpha=0.3)
    cbar = fig.colorbar(scatter, ax=axes[1, 0])
    cbar.set_label("Solar Rad (W/m²)")
    
    # 7d. Diurnal Temperature Cycle (by hour of day)
    df["hour"] = df.index.hour
    df["month"] = df.index.month
    hourly_mean = df.groupby("hour")["temperature_c"].agg(["mean", "min", "max"])
    axes[1, 1].plot(hourly_mean.index, hourly_mean["mean"], color="#2c3e50", label="Mean Diurnal")
    axes[1, 1].fill_between(hourly_mean.index, hourly_mean["min"], hourly_mean["max"], color="#95a5a6", alpha=0.3, label="Min-Max Range")
    axes[1, 1].set_title("Diurnal Temperature Profile (Hourly Average)")
    axes[1, 1].set_xlabel("Hour of Day (UTC)")
    axes[1, 1].set_ylabel("°C")
    axes[1, 1].legend(loc="upper left")
    axes[1, 1].grid(True, alpha=0.3)
    
    # 7e. Monthly Boxplot for Temperature Seasonality
    monthly_temps = [df[df["month"] == m]["temperature_c"].dropna() for m in range(1, 13)]
    axes[2, 0].boxplot(monthly_temps, tick_labels=["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    axes[2, 0].set_title("Monthly Temperature Distribution (Seasonality)")
    axes[2, 0].set_xlabel("Month")
    axes[2, 0].set_ylabel("°C")
    axes[2, 0].grid(True, alpha=0.3)
    
    # 7f. Wind Speed vs Temperature
    axes[2, 1].hist(df["wind_speed_ms"], bins=30, color="#1abc9c", edgecolor="black", alpha=0.7)
    axes[2, 1].set_title("Wind Speed Distribution (m/s)")
    axes[2, 1].set_xlabel("Wind Speed (m/s)")
    axes[2, 1].set_ylabel("Frequency (Hours)")
    axes[2, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = output_dir / f"{location_key}_eda_overview.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    
    report = {
        "location": location_key,
        "total_records": total_records,
        "start_time": str(start_dt),
        "end_time": str(end_dt),
        "expected_hours": expected_hours,
        "missing_timestamps": missing_timestamps,
        "duplicate_timestamps": int(duplicate_count),
        "missing_per_column": missing_per_col,
        "max_temperature_c": float(max_temp),
        "min_temperature_c": float(min_temp),
        "hours_above_40c": int(heat_days_40c),
        "hours_above_45c": int(heat_days_45c),
        "descriptive_statistics": stats_dict,
        "correlation_matrix": corr_matrix,
        "eda_plot_path": str(plot_path)
    }
    
    report_json_path = output_dir / f"{location_key}_eda_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    return report

def run_all_eda():
    config = load_config()
    processed_dir = Path(config["data_pipeline"]["processed_dir"])
    reports_dir = Path(config["data_pipeline"]["reports_dir"])
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    summary_list = []
    for loc_key in config["locations"]:
        csv_file = processed_dir / f"{loc_key}_hourly.csv"
        if csv_file.exists():
            print(f"Running EDA for {loc_key}...")
            res = run_eda_for_location(loc_key, csv_file, reports_dir)
            summary_list.append({
                "location": loc_key,
                "records": res["total_records"],
                "missing": res["missing_timestamps"],
                "max_t": res["max_temperature_c"],
                "min_t": res["min_temperature_c"],
                "hours_ge_40c": res["hours_above_40c"],
                "hours_ge_45c": res["hours_above_45c"]
            })
            
    summary_df = pd.DataFrame(summary_list)
    summary_csv = reports_dir / "eda_cross_location_summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    print("\n--- Cross-Location EDA Summary ---")
    print(summary_df.to_string(index=False))

if __name__ == "__main__":
    run_all_eda()
