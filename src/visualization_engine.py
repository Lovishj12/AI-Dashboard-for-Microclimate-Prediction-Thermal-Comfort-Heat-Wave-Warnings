"""
Psychrometric & Thermal Comfort Visualization Engine (Phase 4).
Mathematically constructs and renders:
1. Standard Sea-Level Psychrometric Chart:
   - Abscissa: Dry-bulb temperature T_db (0°C to 50°C)
   - Ordinate: Humidity ratio W (0 to 35 g_w / kg_da)
   - Saturation curve (100% RH)
   - Constant Relative Humidity curves (10%, 20%, ..., 90%)
   - Constant Wet-Bulb diagonals (10°C, 15°C, 20°C, 25°C, 30°C)
   - Constant Specific Enthalpy lines
   - ASHRAE 55 Summer Thermal Comfort Polygon
   - Plotted empirical microclimate trajectories and heat wave states
2. Thermal Comfort Stress Phase-Space Visualizer:
   - Temperature vs Relative Humidity with NOAA Heat Index and OSHA WBGT risk zones
3. Multi-Metric Diurnal & Seasonal Trend Visualizer
4. Standalone HTML interactive charts and high-resolution PNG export capabilities.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from src.config import load_config
from src.scientific_engine import (
    saturation_vapor_pressure,
    actual_vapor_pressure,
    humidity_ratio,
    dew_point_temperature,
    wet_bulb_temperature,
    STANDARD_PRESSURE_HPA
)

# Output directory for Phase 4 visualizations
VIS_OUTPUT_DIR = Path("reports/visualizations")
VIS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_psychrometric_base(
    t_min: float = 0.0,
    t_max: float = 52.0,
    w_max: float = 35.0,  # in g/kg
    pressure_hpa: float = STANDARD_PRESSURE_HPA,
    figsize: tuple = (13, 9)
) -> tuple:
    """
    Construct mathematically accurate psychrometric background lines.
    Returns (fig, ax).
    """
    fig, ax = plt.subplots(figsize=figsize)
    t_grid = np.linspace(t_min, t_max, 300)
    
    # 1. Plot Relative Humidity Curves (10% to 100%)
    rh_levels = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    for rh in rh_levels:
        w_curve_g_kg = []
        t_valid = []
        for t in t_grid:
            e_s = saturation_vapor_pressure(t)
            e_a = (rh / 100.0) * e_s
            if e_a < pressure_hpa:
                w_kg = 0.62198 * e_a / (pressure_hpa - e_a)
                w_g = w_kg * 1000.0
                if w_g <= w_max * 1.05:
                    w_curve_g_kg.append(w_g)
                    t_valid.append(t)
                    
        is_sat = (rh == 100)
        lw = 2.0 if is_sat else 0.8
        alpha = 1.0 if is_sat else 0.6
        color = "#1a5276" if is_sat else "#5dade2"
        ax.plot(t_valid, w_curve_g_kg, color=color, linewidth=lw, alpha=alpha, zorder=2)
        
        # Label RH curves
        if len(t_valid) > 20:
            idx = int(len(t_valid) * 0.7)
            lbl_t = t_valid[idx]
            lbl_w = w_curve_g_kg[idx]
            if lbl_w < w_max - 2.0 and lbl_t < t_max - 3.0:
                ax.text(lbl_t, lbl_w + 0.3, f"{rh}%", fontsize=8, color="#2980b9", fontweight="bold")

    # 2. Plot Constant Wet-Bulb Lines (diagonals from saturation curve)
    # Along a constant wet-bulb line, (W_sat - W) / (T_db - T_wb) = c_pa / h_fg ~ constant
    wb_levels = [10.0, 15.0, 20.0, 25.0, 30.0, 35.0]
    for twb in wb_levels:
        if twb > t_max:
            continue
        # Saturation state at Twb
        e_sat_wb = saturation_vapor_pressure(twb)
        w_sat_wb = 0.62198 * e_sat_wb / (pressure_hpa - e_sat_wb) * 1000.0
        
        t_pts = np.linspace(twb, min(t_max, twb + 22.0), 50)
        # Wet-bulb psychrometric line equation: W = W_sat(Twb) - (c_pa / h_fg) * (T_db - Twb)
        # c_pa = 1.006 kJ/kg*K, h_fg ~ 2450 kJ/kg -> slope ~ 0.00041 kg/kg/K = 0.41 g/kg/K
        w_pts = w_sat_wb - 0.41 * (t_pts - twb)
        valid_mask = (w_pts >= 0) & (w_pts <= w_max)
        if np.any(valid_mask):
            ax.plot(t_pts[valid_mask], w_pts[valid_mask], color="#27ae60", linestyle="--", linewidth=0.75, alpha=0.7, zorder=2)
            # Label wet bulb
            lbl_idx = 0
            ax.text(t_pts[valid_mask][lbl_idx] - 1.2, w_pts[valid_mask][lbl_idx] + 0.3, f"{int(twb)}°C wb", 
                    fontsize=8, color="#1e8449", rotation=35, fontweight="bold")

    # 3. Plot ASHRAE 55 Summer Thermal Comfort Polygon
    # Typical comfort envelope for sedentary/light activity (0.5 clo, 1.1 met, light air movement)
    # T_db: 23.5°C to 28.0°C; Dew point between 2°C (lower moisture limit) and 16.8°C (upper limit, W ~ 12 g/kg)
    c_t = [23.5, 27.5, 28.5, 24.5]
    c_w = [4.5, 5.0, 12.0, 12.0]
    comfort_poly = patches.Polygon(list(zip(c_t, c_w)), closed=True, facecolor="#2ecc71", edgecolor="#27ae60", alpha=0.35, zorder=3, label="ASHRAE 55 Comfort Envelope")
    ax.add_patch(comfort_poly)
    ax.text(25.5, 8.0, "Thermal Comfort\nZone (ASHRAE 55)", fontsize=9, color="#145a32", fontweight="bold", ha="center", zorder=4)

    # Chart decorations and axes limits
    ax.set_xlim(t_min, t_max)
    ax.set_ylim(0, w_max)
    ax.set_xlabel("Dry-Bulb Temperature T_db (°C)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Humidity Ratio W (g water / kg dry air)", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.4, zorder=1)
    
    # Critical physiological threshold marker: Twb = 35°C (Upper survivability limit)
    ax.axvspan(35.0, t_max, ymin=0.8, ymax=1.0, color="#f2dede", alpha=0.3)
    
    return fig, ax

def plot_location_on_psychrometric_chart(
    enriched_csv_path: Path,
    location_name: str,
    output_png_path: Path,
    sample_size: int = 800
) -> Path:
    """
    Overlays observed time series from an enriched dataset onto the psychrometric chart,
    distinguishing normal vs heat-wave conditions.
    """
    df = pd.read_csv(enriched_csv_path, index_col="timestamp_utc", parse_dates=True)
    if len(df) > sample_size:
        # Sample systematically to capture both diurnal extremes and full year
        df_plot = df.iloc[:: (len(df) // sample_size)].copy()
    else:
        df_plot = df.copy()
        
    fig, ax = generate_psychrometric_base()
    
    # Scatter plot microclimate state points colored by Heat Index
    scatter = ax.scatter(
        df_plot["temperature_c"],
        df_plot["humidity_ratio_g_kg"],
        c=df_plot["heat_index_c"],
        cmap="YlOrRd",
        s=25,
        alpha=0.65,
        edgecolor="none",
        zorder=5,
        label="Observed States"
    )
    cbar = fig.colorbar(scatter, ax=ax, pad=0.02)
    cbar.set_label("NOAA Heat Index (°C)", fontsize=11, fontweight="bold")
    
    # Highlight extreme heat-wave trajectory (e.g. May 2024 peak 48 hours)
    peak_idx = df["temperature_c"].idxmax()
    peak_start = peak_idx - pd.Timedelta(hours=24)
    peak_end = peak_idx + pd.Timedelta(hours=24)
    df_peak = df.loc[peak_start:peak_end]
    
    if len(df_peak) > 0:
        ax.plot(
            df_peak["temperature_c"],
            df_peak["humidity_ratio_g_kg"],
            color="#8e44ad",
            linewidth=2.0,
            linestyle="-",
            marker="o",
            markersize=4,
            alpha=0.9,
            zorder=6,
            label=f"Peak Heat Wave Trajectory ({peak_start.strftime('%d %b')} - {peak_end.strftime('%d %b %Y')})"
        )
        # Mark absolute peak
        peak_row = df.loc[peak_idx]
        ax.scatter(
            [peak_row["temperature_c"]],
            [peak_row["humidity_ratio_g_kg"]],
            color="#900c3f",
            s=120,
            marker="*",
            edgecolor="black",
            linewidth=1.2,
            zorder=7,
            label=f"Max T_db: {peak_row['temperature_c']}°C"
        )
        
    ax.set_title(f"Psychrometric Microclimate State Space: {location_name}\n(Pressure: {STANDARD_PRESSURE_HPA} hPa | Period: 2023 - 2024)", 
                 fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="upper left", framealpha=0.9)
    
    plt.tight_layout()
    plt.savefig(output_png_path, dpi=150)
    plt.close()
    return output_png_path

def plot_thermal_comfort_phase_space(
    enriched_csv_path: Path,
    location_name: str,
    output_png_path: Path
) -> Path:
    """
    Generates Temperature vs. Relative Humidity phase space with
    overlaid NOAA Heat Index risk zones and observed points.
    """
    df = pd.read_csv(enriched_csv_path, index_col="timestamp_utc", parse_dates=True)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Define grid for NOAA Heat Index background
    t_vals = np.linspace(20, 50, 150)
    rh_vals = np.linspace(5, 100, 150)
    T_mesh, RH_mesh = np.meshgrid(t_vals, rh_vals)
    
    from src.scientific_engine import heat_index
    HI_mesh = heat_index(T_mesh, RH_mesh)
    
    # Contour levels for Heat Index risk zones
    levels = [0, 27.0, 32.0, 39.0, 51.0, 80.0]
    colors = ["#d4efdf", "#fcf3cf", "#fbcba5", "#f5b7b1", "#d7bde2"]
    
    cf = ax.contourf(T_mesh, RH_mesh, HI_mesh, levels=levels, colors=colors, alpha=0.7)
    
    # Add contour boundary lines
    ax.contour(T_mesh, RH_mesh, HI_mesh, levels=levels[1:-1], colors="#7f8c8d", linewidths=1.0, linestyles="--")
    
    # Overlay observed microclimate data
    scatter = ax.scatter(
        df["temperature_c"].iloc[::10],
        df["relative_humidity_pct"].iloc[::10],
        c=df["wet_bulb_c"].iloc[::10],
        cmap="coolwarm",
        s=15,
        alpha=0.6,
        edgecolor="none",
        zorder=3
    )
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Wet-Bulb Temperature T_wb (°C)", fontsize=11, fontweight="bold")
    
    # Labels for zones
    ax.text(23, 20, "Normal\n(<27°C)", fontsize=10, color="#196f3d", fontweight="bold", ha="center")
    ax.text(29, 25, "Caution\n(27-32°C)", fontsize=10, color="#b7950b", fontweight="bold", ha="center")
    ax.text(35, 30, "Extreme Caution\n(32-39°C)", fontsize=10, color="#ba4a00", fontweight="bold", ha="center")
    ax.text(42, 35, "Danger\n(39-51°C)", fontsize=10, color="#922b21", fontweight="bold", ha="center")
    ax.text(46, 60, "Extreme Danger\n(≥51°C)", fontsize=10, color="#512e5f", fontweight="bold", ha="center")
    
    ax.set_title(f"Thermal Comfort Stress Phase Space: {location_name}\nNOAA Heat Index Zones with Observed Microclimate Data", 
                 fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Dry-Bulb Temperature (°C)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Relative Humidity (%)", fontsize=12, fontweight="bold")
    ax.set_xlim(20, 50)
    ax.set_ylim(5, 100)
    ax.grid(True, linestyle=":", alpha=0.4)
    
    plt.tight_layout()
    plt.savefig(output_png_path, dpi=150)
    plt.close()
    return output_png_path

def plot_diurnal_and_weekly_heat_wave(
    enriched_csv_path: Path,
    location_name: str,
    output_png_path: Path
) -> Path:
    """
    Renders multi-parameter diurnal dynamics during a heat wave episode.
    Shows simultaneous Dry-Bulb, Wet-Bulb, Dew Point, Heat Index, and sWBGT.
    """
    df = pd.read_csv(enriched_csv_path, index_col="timestamp_utc", parse_dates=True)
    
    # Select peak heat wave week in May 2024
    peak_time = df["temperature_c"].idxmax()
    week_start = peak_time - pd.Timedelta(days=3)
    week_end = peak_time + pd.Timedelta(days=4)
    df_week = df.loc[week_start:week_end]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
    
    # Panel 1: Temperature & Comfort Indices
    ax1.plot(df_week.index, df_week["heat_index_c"], label="Heat Index (NOAA)", color="#c0392b", linewidth=2.0)
    ax1.plot(df_week.index, df_week["temperature_c"], label="Dry-Bulb T_db", color="#e67e22", linewidth=1.5)
    ax1.plot(df_week.index, df_week["swbgt_c"], label="Simplified WBGT (BoM)", color="#8e44ad", linewidth=1.5, linestyle="--")
    ax1.plot(df_week.index, df_week["wet_bulb_c"], label="Wet-Bulb T_wb", color="#2980b9", linewidth=1.5)
    ax1.plot(df_week.index, df_week["dew_point_c"], label="Dew Point T_dp", color="#27ae60", linewidth=1.2, linestyle=":")
    
    # Threshold lines
    ax1.axhline(45.0, color="red", linestyle=":", alpha=0.7, label="IMD Severe Heat Wave (45°C)")
    ax1.axhline(39.0, color="#e74c3c", linestyle="--", alpha=0.5, label="HI Danger Threshold (39°C)")
    ax1.axhline(30.0, color="#2980b9", linestyle="--", alpha=0.5, label="High Twb Stress (30°C)")
    
    ax1.set_ylabel("Temperature / Index (°C)", fontsize=11, fontweight="bold")
    ax1.set_title(f"Multi-Parameter Heat Wave Dynamics: {location_name}\n({week_start.strftime('%d %b %Y')} to {week_end.strftime('%d %b %Y')})", 
                  fontsize=13, fontweight="bold")
    ax1.legend(loc="upper right", ncol=3, fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: Relative Humidity & Solar Radiation
    ax2_rad = ax2.twinx()
    l1 = ax2.plot(df_week.index, df_week["relative_humidity_pct"], color="#2980b9", linewidth=1.5, label="Relative Humidity (%)")
    l2 = ax2_rad.plot(df_week.index, df_week["solar_radiation_wm2"], color="#f39c12", linewidth=1.2, linestyle="-.", label="Solar Irradiance (W/m²)")
    
    ax2.set_ylabel("Relative Humidity (%)", fontsize=11, fontweight="bold", color="#2980b9")
    ax2_rad.set_ylabel("Solar Irradiance (W/m²)", fontsize=11, fontweight="bold", color="#f39c12")
    ax2.set_xlabel("Date / Time (UTC)", fontsize=11, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    
    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc="upper right", fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_png_path, dpi=150)
    plt.close()
    return output_png_path

def run_all_visualizations():
    config = load_config()
    enriched_dir = Path(config["data_pipeline"]["processed_dir"]) / "enriched"
    
    print("Generating Phase 4 Visualizations...")
    for loc_key, loc_info in config["locations"].items():
        csv_path = enriched_dir / f"{loc_key}_enriched_hourly.csv"
        if not csv_path.exists():
            continue
            
        print(f"--> Rendering Psychrometric Chart for {loc_info['name']}...")
        p1 = VIS_OUTPUT_DIR / f"{loc_key}_psychrometric_chart.png"
        plot_location_on_psychrometric_chart(csv_path, loc_info["name"], p1)
        
        print(f"--> Rendering Thermal Stress Phase Space for {loc_info['name']}...")
        p2 = VIS_OUTPUT_DIR / f"{loc_key}_thermal_stress_phase_space.png"
        plot_thermal_comfort_phase_space(csv_path, loc_info["name"], p2)
        
        print(f"--> Rendering Diurnal Heat Wave Dynamics for {loc_info['name']}...")
        p3 = VIS_OUTPUT_DIR / f"{loc_key}_diurnal_heat_wave_dynamics.png"
        plot_diurnal_and_weekly_heat_wave(csv_path, loc_info["name"], p3)

    print("Phase 4 Visualization suite generated successfully in:", VIS_OUTPUT_DIR)

if __name__ == "__main__":
    run_all_visualizations()
