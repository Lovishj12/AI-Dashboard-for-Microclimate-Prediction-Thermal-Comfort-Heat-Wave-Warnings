"""
Baseline Prediction Engine (Phase 5).
Formulates the time-series forecasting problem for microclimate and thermal comfort:
1. Physical Forecasting Target:
   - Primary: Temperature T(t + h) and Relative Humidity RH(t + h) for horizons h in {1, 3, 6, 24 hours}.
   - Derived Target: Future Heat Index HI(t + h) and Future Wet-Bulb Twb(t + h) computed via validated Scientific Engine.
2. Temporal Feature Engineering (Strictly preventing data leakage):
   - Cyclic time features: hour_sin, hour_cos, month_sin, month_cos
   - Lag features: T(t-1), T(t-2), T(t-3), T(t-24), RH(t-1), RH(t-24), etc.
   - Rolling window features: 3h, 6h, 24h rolling mean, min, max, std
   - Temporal delta rates: (T(t) - T(t-1)), (T(t) - T(t-24))
3. Chronological Time-Series Train/Validation/Test Split:
   - Train: 2023-01-01 to 2023-12-31 (12 months = 8,760 hours)
   - Validation: 2024-01-01 to 2024-03-31 (3 months = 2,184 hours)
   - Test: 2024-04-01 to 2024-06-30 (3 months = 2,184 hours, capturing the severe 2024 heat wave)
4. Baseline Models:
   - Baseline 1: Naive Persistence Benchmark (y_hat(t+h) = y(t))
   - Baseline 2: 24-Hour Seasonal Diurnal Persistence Benchmark (y_hat(t+h) = y(t + h - 24))
   - Baseline 3: Linear Ridge Regression with engineered temporal/lag features
5. Evaluation Metrics: MAE, RMSE, R^2, and Peak Heat Wave Error Analysis.
"""

from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
import matplotlib.pyplot as plt

from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.config import load_config
from src.scientific_engine import heat_index, wet_bulb_temperature

MODELS_DIR = Path("models/baseline")
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = Path("reports/ml")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def create_time_series_features(df: pd.DataFrame, horizons: List[int] = [1, 3, 6, 24]) -> pd.DataFrame:
    """
    Constructs leak-free lag, rolling, and cyclical features for time series forecasting.
    Only uses information strictly at or before time t to predict t + h.
    """
    feat_df = df.copy()
    
    # 1. Cyclical Time Features (Hour of Day and Month of Year)
    hour = feat_df.index.hour
    month = feat_df.index.month
    
    feat_df["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    feat_df["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
    feat_df["month_sin"] = np.sin(2 * np.pi * (month - 1) / 12.0)
    feat_df["month_cos"] = np.cos(2 * np.pi * (month - 1) / 12.0)
    
    # 2. Lagged Features for Core Environmental Predictors
    for lag in [1, 2, 3, 6, 12, 24]:
        feat_df[f"temp_lag_{lag}"] = feat_df["temperature_c"].shift(lag)
        feat_df[f"rh_lag_{lag}"] = feat_df["relative_humidity_pct"].shift(lag)
        feat_df[f"solar_lag_{lag}"] = feat_df["solar_radiation_wm2"].shift(lag)
        feat_df[f"wind_lag_{lag}"] = feat_df["wind_speed_ms"].shift(lag)
        
    # 3. Rolling Statistics (Using past values only: shift(1) ensures no lookahead bias)
    for window in [3, 6, 24]:
        feat_df[f"temp_roll_mean_{window}"] = feat_df["temperature_c"].shift(1).rolling(window).mean()
        feat_df[f"temp_roll_std_{window}"] = feat_df["temperature_c"].shift(1).rolling(window).std()
        feat_df[f"temp_roll_max_{window}"] = feat_df["temperature_c"].shift(1).rolling(window).max()
        feat_df[f"temp_roll_min_{window}"] = feat_df["temperature_c"].shift(1).rolling(window).min()
        
        feat_df[f"rh_roll_mean_{window}"] = feat_df["relative_humidity_pct"].shift(1).rolling(window).mean()
        
    # 4. Difference / Rate of Change Features
    feat_df["temp_diff_1h"] = feat_df["temperature_c"].shift(1) - feat_df["temperature_c"].shift(2)
    feat_df["temp_diff_24h"] = feat_df["temperature_c"].shift(1) - feat_df["temperature_c"].shift(25)
    feat_df["rh_diff_1h"] = feat_df["relative_humidity_pct"].shift(1) - feat_df["relative_humidity_pct"].shift(2)
    
    # 5. Future Prediction Targets for Specified Horizons
    for h in horizons:
        feat_df[f"target_temp_h{h}"] = feat_df["temperature_c"].shift(-h)
        feat_df[f"target_rh_h{h}"] = feat_df["relative_humidity_pct"].shift(-h)
        feat_df[f"target_hi_h{h}"] = feat_df["heat_index_c"].shift(-h)
        feat_df[f"target_twb_h{h}"] = feat_df["wet_bulb_c"].shift(-h)
        
    # Drop warm-up rows containing NaNs from lagging (25 hours) and lookahead rows at the very end
    max_lag = 25
    max_horizon = max(horizons)
    clean_df = feat_df.iloc[max_lag:-max_horizon].copy()
    
    return clean_df

def temporal_train_val_test_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Strict chronological time-based split:
    - Train: 2023-01-01 to 2023-12-31
    - Val:   2024-01-01 to 2024-03-31
    - Test:  2024-04-01 to 2024-06-30 (Summer heat wave evaluation)
    """
    train = df.loc["2023-01-01":"2023-12-31"].copy()
    val = df.loc["2024-01-01":"2024-03-31"].copy()
    test = df.loc["2024-04-01":"2024-06-30"].copy()
    return train, val, test

def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes standard regression metrics.
    """
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    return {
        "MAE": round(float(mae), 3),
        "RMSE": round(float(rmse), 3),
        "R2": round(float(r2), 4)
    }

def train_and_evaluate_baselines(location_key: str = "kharagpur", horizon: int = 1) -> Dict:
    """
    Trains Baseline Ridge regression and compares against Naive Persistence benchmarks
    for horizon h (e.g. 1 hour ahead or 6 hours ahead).
    """
    config = load_config()
    enriched_dir = Path(config["data_pipeline"]["processed_dir"]) / "enriched"
    csv_path = enriched_dir / f"{location_key}_enriched_hourly.csv"
    
    raw_df = pd.read_csv(csv_path, index_col="timestamp_utc", parse_dates=True)
    feat_df = create_time_series_features(raw_df, horizons=[1, 3, 6, 24])
    
    train_df, val_df, test_df = temporal_train_val_test_split(feat_df)
    
    target_col_t = f"target_temp_h{horizon}"
    target_col_rh = f"target_rh_h{horizon}"
    target_col_hi = f"target_hi_h{horizon}"
    
    # Feature columns: exclude target columns and raw metadata
    exclude_cols = [c for c in feat_df.columns if c.startswith("target_")] + ["location"]
    feature_cols = [c for c in feat_df.columns if c not in exclude_cols]
    
    X_train = train_df[feature_cols]
    y_train_t = train_df[target_col_t]
    y_train_rh = train_df[target_col_rh]
    
    X_test = test_df[feature_cols]
    y_test_t = test_df[target_col_t]
    y_test_rh = test_df[target_col_rh]
    y_test_hi = test_df[target_col_hi]
    
    # -------------------------------------------------------------
    # Benchmark 1: Naive Persistence (y_pred(t+h) = y(t))
    # -------------------------------------------------------------
    pred_persist_t = test_df["temperature_c"].values
    pred_persist_rh = test_df["relative_humidity_pct"].values
    pred_persist_hi = heat_index(pred_persist_t, pred_persist_rh)
    
    metrics_persist_t = evaluate_predictions(y_test_t.values, pred_persist_t)
    metrics_persist_hi = evaluate_predictions(y_test_hi.values, pred_persist_hi)
    
    # -------------------------------------------------------------
    # Benchmark 2: 24h Diurnal Seasonal Persistence
    # (y_pred(t+h) = y(t + h - 24) = lag(24 - h))
    # -------------------------------------------------------------
    if f"temp_lag_{24}" in test_df.columns:
        pred_diurnal_t = test_df[f"temp_lag_{24}"].values
        pred_diurnal_rh = test_df[f"rh_lag_{24}"].values
        pred_diurnal_hi = heat_index(pred_diurnal_t, pred_diurnal_rh)
        metrics_diurnal_t = evaluate_predictions(y_test_t.values, pred_diurnal_t)
        metrics_diurnal_hi = evaluate_predictions(y_test_hi.values, pred_diurnal_hi)
    else:
        metrics_diurnal_t = None
        metrics_diurnal_hi = None
        
    # -------------------------------------------------------------
    # Baseline 3: Ridge Regression with Standardized Features
    # -------------------------------------------------------------
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Model for Temperature
    model_t = Ridge(alpha=10.0)
    model_t.fit(X_train_scaled, y_train_t)
    pred_ridge_t = model_t.predict(X_test_scaled)
    
    # Model for Relative Humidity
    model_rh = Ridge(alpha=10.0)
    model_rh.fit(X_train_scaled, y_train_rh)
    pred_ridge_rh = np.clip(model_rh.predict(X_test_scaled), 0.0, 100.0)
    
    # Derived Physical Forecast: Heat Index from (pred_t, pred_rh)
    pred_ridge_hi = heat_index(pred_ridge_t, pred_ridge_rh)
    
    metrics_ridge_t = evaluate_predictions(y_test_t.values, pred_ridge_t)
    metrics_ridge_rh = evaluate_predictions(y_test_rh.values, pred_ridge_rh)
    metrics_ridge_hi = evaluate_predictions(y_test_hi.values, pred_ridge_hi)
    
    # Save Model Artifacts
    model_artifact = {
        "scaler": scaler,
        "model_t": model_t,
        "model_rh": model_rh,
        "feature_cols": feature_cols,
        "location": location_key,
        "horizon": horizon
    }
    artifact_path = MODELS_DIR / f"{location_key}_baseline_ridge_h{horizon}.joblib"
    joblib.dump(model_artifact, artifact_path)
    
    # -------------------------------------------------------------
    # Diagnostic Error Plot during May 2024 Heat Wave
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    # Zoom in to a 7-day severe heat wave window in May 2024
    zoom_start = "2024-05-18"
    zoom_end = "2024-05-25"
    mask = (test_df.index >= zoom_start) & (test_df.index <= zoom_end)
    zoom_idx = test_df.index[mask]
    
    # Temperature forecast comparison
    ax1.plot(zoom_idx, y_test_t[mask], label="Observed T(t+h)", color="black", linewidth=2.0)
    ax1.plot(zoom_idx, pred_persist_t[mask], label="Naive Persistence", color="#95a5a6", linestyle=":", linewidth=1.5)
    ax1.plot(zoom_idx, pred_ridge_t[mask], label=f"Baseline Ridge (h={horizon}h)", color="#e74c3c", linewidth=1.8)
    ax1.set_ylabel("Temperature (°C)", fontweight="bold")
    ax1.set_title(f"Baseline Forecast Evaluation (h={horizon}h): {location_key.upper()} Severe Heat Wave (May 2024)", fontweight="bold")
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)
    
    # Heat Index forecast comparison
    ax2.plot(zoom_idx, y_test_hi[mask], label="Observed Heat Index", color="black", linewidth=2.0)
    ax2.plot(zoom_idx, pred_ridge_hi[mask], label=f"Ridge-Engine Derived HI", color="#8e44ad", linewidth=1.8)
    ax2.axhline(39.0, color="orange", linestyle="--", label="Danger Threshold (39°C)")
    ax2.axhline(51.0, color="red", linestyle="--", label="Extreme Danger (51°C)")
    ax2.set_ylabel("Heat Index (°C)", fontweight="bold")
    ax2.set_xlabel("Date (UTC)", fontweight="bold")
    ax2.legend(loc="upper right")
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = REPORTS_DIR / f"{location_key}_baseline_h{horizon}_forecast_eval.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    
    summary = {
        "location": location_key,
        "horizon_hours": horizon,
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "metrics": {
            "temperature": {
                "naive_persistence": metrics_persist_t,
                "seasonal_diurnal": metrics_diurnal_t,
                "baseline_ridge": metrics_ridge_t
            },
            "relative_humidity": {
                "baseline_ridge": metrics_ridge_rh
            },
            "heat_index": {
                "naive_persistence": metrics_persist_hi,
                "baseline_ridge": metrics_ridge_hi
            }
        },
        "plot_path": str(plot_path),
        "model_artifact": str(artifact_path)
    }
    
    with open(REPORTS_DIR / f"{location_key}_baseline_h{horizon}_report.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    return summary

def run_all_baselines():
    config = load_config()
    all_summaries = []
    
    for loc in config["locations"]:
        for h in [1, 3, 6, 24]:
            print(f"Training Baseline Ridge Model for {loc} at horizon h={h} hours...")
            res = train_and_evaluate_baselines(loc, horizon=h)
            all_summaries.append({
                "location": loc,
                "horizon": h,
                "Persist_T_MAE": res["metrics"]["temperature"]["naive_persistence"]["MAE"],
                "Ridge_T_MAE": res["metrics"]["temperature"]["baseline_ridge"]["MAE"],
                "Ridge_T_RMSE": res["metrics"]["temperature"]["baseline_ridge"]["RMSE"],
                "Ridge_T_R2": res["metrics"]["temperature"]["baseline_ridge"]["R2"],
                "Ridge_HI_MAE": res["metrics"]["heat_index"]["baseline_ridge"]["MAE"]
            })
            
    summary_df = pd.DataFrame(all_summaries)
    summary_csv = REPORTS_DIR / "baseline_models_summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    print("\n--- Baseline Model Performance Summary Across Horizons ---")
    print(summary_df.to_string(index=False))

if __name__ == "__main__":
    run_all_baselines()
