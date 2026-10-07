"""
Advanced AI/ML & Model Comparison Engine (Phase 6).
Evaluates and compares multi-model architectures for microclimate forecasting:
1. Candidate Models:
   - Baseline: Ridge Regression (from Phase 5)
   - Non-linear Ensemble 1: Random Forest Regressor (with tuned trees and depth)
   - Non-linear Ensemble 2: HistGradientBoostingRegressor (fast, robust gradient boosting)
2. Evaluation Metrics:
   - Regression: MAE, RMSE, R^2
   - Extreme Heat Wave Performance: MAE during extreme heat events (T >= 40°C)
   - Safety Classification: Warning state classification accuracy, Precision, Recall, F1 for Danger states (HI >= 39°C)
3. Model Explainability:
   - Permutation / Tree Feature Importance analysis identifying primary physical drivers
4. Final Model Selection:
   - Evidence-based champion selection per location and horizon
   - Serializes champion model artifacts into models/champion/
"""

from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt

from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

from src.config import load_config
from src.scientific_engine import heat_index, classify_heat_index
from src.baseline_model import create_time_series_features, temporal_train_val_test_split

ADVANCED_MODELS_DIR = Path("models/advanced")
ADVANCED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
CHAMPION_MODELS_DIR = Path("models/champion")
CHAMPION_MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = Path("reports/ml")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def train_and_compare_models(location_key: str = "new_delhi", horizon: int = 1) -> Dict:
    """
    Trains Ridge, Random Forest, and HistGradientBoosting for horizon h,
    evaluates overall regression, extreme heat subset metrics, safety recall,
    and extracts feature importance.
    """
    config = load_config()
    enriched_dir = Path(config["data_pipeline"]["processed_dir"]) / "enriched"
    csv_path = enriched_dir / f"{location_key}_enriched_hourly.csv"
    
    raw_df = pd.read_csv(csv_path, index_col="timestamp_utc", parse_dates=True)
    feat_df = create_time_series_features(raw_df, horizons=[horizon])
    
    train_df, val_df, test_df = temporal_train_val_test_split(feat_df)
    
    target_col_t = f"target_temp_h{horizon}"
    target_col_rh = f"target_rh_h{horizon}"
    target_col_hi = f"target_hi_h{horizon}"
    
    exclude_cols = [c for c in feat_df.columns if c.startswith("target_")] + ["location"]
    feature_cols = [c for c in feat_df.columns if c not in exclude_cols]
    
    X_train = train_df[feature_cols]
    y_train_t = train_df[target_col_t]
    y_train_rh = train_df[target_col_rh]
    
    X_test = test_df[feature_cols]
    y_test_t = test_df[target_col_t].values
    y_test_rh = test_df[target_col_rh].values
    y_test_hi = test_df[target_col_hi].values
    
    # Ground truth safety alert categories for Test set
    # Binary classification: Danger / Extreme Danger (HI >= 39°C) vs Non-Danger (HI < 39°C)
    y_test_danger_binary = (y_test_hi >= 39.0).astype(int)
    
    # Extreme heat test mask (Observed T >= 40°C)
    extreme_mask = y_test_t >= 40.0
    
    # -------------------------------------------------------------
    # 1. Ridge Regression (Baseline Reference)
    # -------------------------------------------------------------
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    ridge_t = Ridge(alpha=10.0)
    ridge_t.fit(X_train_scaled, y_train_t)
    pred_ridge_t = ridge_t.predict(X_test_scaled)
    
    ridge_rh = Ridge(alpha=10.0)
    ridge_rh.fit(X_train_scaled, y_train_rh)
    pred_ridge_rh = np.clip(ridge_rh.predict(X_test_scaled), 0.0, 100.0)
    pred_ridge_hi = heat_index(pred_ridge_t, pred_ridge_rh)
    
    # -------------------------------------------------------------
    # 2. Random Forest Regressor
    # -------------------------------------------------------------
    rf_t = RandomForestRegressor(n_estimators=100, max_depth=14, min_samples_split=4, random_state=42, n_jobs=-1)
    rf_t.fit(X_train, y_train_t)
    pred_rf_t = rf_t.predict(X_test)
    
    rf_rh = RandomForestRegressor(n_estimators=100, max_depth=14, min_samples_split=4, random_state=42, n_jobs=-1)
    rf_rh.fit(X_train, y_train_rh)
    pred_rf_rh = np.clip(rf_rh.predict(X_test), 0.0, 100.0)
    pred_rf_hi = heat_index(pred_rf_t, pred_rf_rh)
    
    # -------------------------------------------------------------
    # 3. HistGradientBoostingRegressor (Gradient Boosted Trees)
    # -------------------------------------------------------------
    hgb_t = HistGradientBoostingRegressor(max_iter=150, max_depth=10, learning_rate=0.08, random_state=42)
    hgb_t.fit(X_train, y_train_t)
    pred_hgb_t = hgb_t.predict(X_test)
    
    hgb_rh = HistGradientBoostingRegressor(max_iter=150, max_depth=10, learning_rate=0.08, random_state=42)
    hgb_rh.fit(X_train, y_train_rh)
    pred_hgb_rh = np.clip(hgb_rh.predict(X_test), 0.0, 100.0)
    pred_hgb_hi = heat_index(pred_hgb_t, pred_hgb_rh)
    
    # -------------------------------------------------------------
    # Metrics Computation Function
    # -------------------------------------------------------------
    def compute_all_metrics(pred_t, pred_rh, pred_hi):
        # Overall regression
        mae_t = mean_absolute_error(y_test_t, pred_t)
        rmse_t = np.sqrt(mean_squared_error(y_test_t, pred_t))
        r2_t = r2_score(y_test_t, pred_t)
        
        mae_hi = mean_absolute_error(y_test_hi, pred_hi)
        rmse_hi = np.sqrt(mean_squared_error(y_test_hi, pred_hi))
        
        # Extreme heat metrics (T >= 40°C)
        if np.any(extreme_mask):
            extreme_mae_t = mean_absolute_error(y_test_t[extreme_mask], pred_t[extreme_mask])
            extreme_mae_hi = mean_absolute_error(y_test_hi[extreme_mask], pred_hi[extreme_mask])
        else:
            extreme_mae_t = None
            extreme_mae_hi = None
            
        # Danger Safety classification (HI >= 39°C)
        pred_danger_binary = (pred_hi >= 39.0).astype(int)
        prec = precision_score(y_test_danger_binary, pred_danger_binary, zero_division=0)
        rec = recall_score(y_test_danger_binary, pred_danger_binary, zero_division=0)
        f1 = f1_score(y_test_danger_binary, pred_danger_binary, zero_division=0)
        cm = confusion_matrix(y_test_danger_binary, pred_danger_binary).tolist()
        
        return {
            "MAE_T": round(float(mae_t), 3),
            "RMSE_T": round(float(rmse_t), 3),
            "R2_T": round(float(r2_t), 4),
            "MAE_HI": round(float(mae_hi), 3),
            "RMSE_HI": round(float(rmse_hi), 3),
            "Extreme_MAE_T": round(float(extreme_mae_t), 3) if extreme_mae_t is not None else None,
            "Extreme_MAE_HI": round(float(extreme_mae_hi), 3) if extreme_mae_hi is not None else None,
            "Danger_Precision": round(float(prec), 4),
            "Danger_Recall": round(float(rec), 4),
            "Danger_F1": round(float(f1), 4),
            "Confusion_Matrix": cm
        }
        
    metrics_ridge = compute_all_metrics(pred_ridge_t, pred_ridge_rh, pred_ridge_hi)
    metrics_rf = compute_all_metrics(pred_rf_t, pred_rf_rh, pred_rf_hi)
    metrics_hgb = compute_all_metrics(pred_hgb_t, pred_hgb_rh, pred_hgb_hi)
    
    # -------------------------------------------------------------
    # Champion Selection (Rank by composite: R2, RMSE_T, and Danger_F1)
    # -------------------------------------------------------------
    models_pool = {
        "Ridge": (metrics_ridge, (scaler, ridge_t, ridge_rh)),
        "RandomForest": (metrics_rf, (None, rf_t, rf_rh)),
        "HistGradientBoosting": (metrics_hgb, (None, hgb_t, hgb_rh))
    }
    
    # Select champion by lowest overall RMSE_T with tie-break on Danger_F1
    champion_name = min(models_pool.keys(), key=lambda k: (models_pool[k][0]["RMSE_T"], -models_pool[k][0]["Danger_F1"]))
    champion_metrics = models_pool[champion_name][0]
    champ_scaler, champ_t, champ_rh = models_pool[champion_name][1]
    
    # Save Champion Model Artifact
    champ_artifact = {
        "model_type": champion_name,
        "location": location_key,
        "horizon": horizon,
        "scaler": champ_scaler,
        "model_t": champ_t,
        "model_rh": champ_rh,
        "feature_cols": feature_cols,
        "metrics": champion_metrics
    }
    champ_path = CHAMPION_MODELS_DIR / f"{location_key}_champion_h{horizon}.joblib"
    joblib.dump(champ_artifact, champ_path)
    
    # -------------------------------------------------------------
    # Feature Importance (Random Forest MDI & Tree Insights)
    # -------------------------------------------------------------
    importances = rf_t.feature_importances_
    feat_imp_series = pd.Series(importances, index=feature_cols).sort_values(ascending=False)
    top_features = feat_imp_series.head(10).to_dict()
    
    # Save Feature Importance Plot
    plt.figure(figsize=(10, 6))
    feat_imp_series.head(10).plot(kind="barh", color="#2980b9")
    plt.title(f"Top 10 Feature Importances (Random Forest h={horizon}h): {location_key.upper()}", fontweight="bold")
    plt.xlabel("Mean Decrease in Impurity (MDI)")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    feat_imp_path = REPORTS_DIR / f"{location_key}_h{horizon}_feature_importance.png"
    plt.savefig(feat_imp_path, dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # Heat Wave Prediction Comparison Plot (Champion vs Baselines)
    # -------------------------------------------------------------
    zoom_start = "2024-05-18"
    zoom_end = "2024-05-25"
    mask = (test_df.index >= zoom_start) & (test_df.index <= zoom_end)
    zoom_idx = test_df.index[mask]
    
    plt.figure(figsize=(14, 7))
    plt.plot(zoom_idx, y_test_t[mask], label="Observed T(t+h)", color="black", linewidth=2.2)
    plt.plot(zoom_idx, pred_ridge_t[mask], label=f"Ridge (RMSE: {metrics_ridge['RMSE_T']}°C)", color="#95a5a6", linestyle="--")
    plt.plot(zoom_idx, pred_rf_t[mask], label=f"Random Forest (RMSE: {metrics_rf['RMSE_T']}°C)", color="#27ae60", linestyle=":")
    plt.plot(zoom_idx, pred_hgb_t[mask], label=f"HistGradientBoosting (RMSE: {metrics_hgb['RMSE_T']}°C)", color="#e74c3c", linewidth=1.8)
    
    plt.axhline(45.0, color="red", linestyle=":", label="IMD Severe Heat Wave (45°C)")
    plt.title(f"Model Comparison on Severe Heat Wave (h={horizon}h): {location_key.upper()} (May 2024)\nChampion Selected: {champion_name}", 
              fontweight="bold", fontsize=13)
    plt.ylabel("Temperature (°C)", fontweight="bold")
    plt.xlabel("Date (UTC)", fontweight="bold")
    plt.legend(loc="upper right", framealpha=0.9)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    comp_plot_path = REPORTS_DIR / f"{location_key}_h{horizon}_model_comparison.png"
    plt.savefig(comp_plot_path, dpi=150)
    plt.close()
    
    result_summary = {
        "location": location_key,
        "horizon_hours": horizon,
        "champion": champion_name,
        "comparison": {
            "Ridge": metrics_ridge,
            "RandomForest": metrics_rf,
            "HistGradientBoosting": metrics_hgb
        },
        "top_features": top_features,
        "champion_artifact_path": str(champ_path),
        "comparison_plot_path": str(comp_plot_path),
        "feature_importance_plot_path": str(feat_imp_path)
    }
    
    with open(REPORTS_DIR / f"{location_key}_h{horizon}_comparison_report.json", "w", encoding="utf-8") as f:
        json.dump(result_summary, f, indent=2)
        
    return result_summary

def run_all_comparisons():
    config = load_config()
    all_records = []
    
    print("Executing Phase 6 Advanced AI/ML Model Comparison...")
    for loc in config["locations"]:
        for h in [1, 3, 6, 24]:
            print(f"Comparing models for {loc} at horizon h={h} hours...")
            res = train_and_compare_models(loc, horizon=h)
            champ = res["champion"]
            m_champ = res["comparison"][champ]
            m_ridge = res["comparison"]["Ridge"]
            
            all_records.append({
                "Location": loc,
                "Horizon": h,
                "Champion": champ,
                "Ridge_RMSE": m_ridge["RMSE_T"],
                "Champ_RMSE": m_champ["RMSE_T"],
                "Champ_R2": m_champ["R2_T"],
                "Champ_MAE_T": m_champ["MAE_T"],
                "Champ_Extreme_MAE": m_champ["Extreme_MAE_T"],
                "Champ_Danger_Recall": m_champ["Danger_Recall"],
                "Champ_Danger_F1": m_champ["Danger_F1"]
            })
            
    summary_df = pd.DataFrame(all_records)
    summary_csv = REPORTS_DIR / "advanced_model_comparison_summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    print("\n--- Advanced ML Champion Model Summary Across Horizons ---")
    print(summary_df.to_string(index=False))

if __name__ == "__main__":
    run_all_comparisons()
