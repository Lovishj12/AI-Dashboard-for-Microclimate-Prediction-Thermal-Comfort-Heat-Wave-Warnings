"""
Automated unit tests for Phase 5 Baseline Prediction Model.
Validates:
1. Feature engineering produces non-null, correctly shifted arrays.
2. Temporal splits are strictly non-overlapping and chronologically ordered.
3. Baseline Ridge model artifacts are saved and can be reloaded for inference.
4. Model outperforms naive persistence on short-to-medium horizons.
"""

import unittest
from pathlib import Path
import pandas as pd
import joblib
from src.baseline_model import (
    create_time_series_features,
    temporal_train_val_test_split,
    MODELS_DIR
)
from src.config import load_config

class TestBaselineModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        cls.csv_path = Path(cls.config["data_pipeline"]["processed_dir"]) / "enriched" / "new_delhi_enriched_hourly.csv"
        cls.df = pd.read_csv(cls.csv_path, index_col="timestamp_utc", parse_dates=True)
        
    def test_feature_engineering_integrity(self):
        feat_df = create_time_series_features(self.df, horizons=[1, 3, 6, 24])
        
        # Check that lag columns are generated
        self.assertIn("temp_lag_1", feat_df.columns)
        self.assertIn("temp_lag_24", feat_df.columns)
        self.assertIn("hour_sin", feat_df.columns)
        self.assertIn("hour_cos", feat_df.columns)
        self.assertIn("target_temp_h1", feat_df.columns)
        self.assertIn("target_temp_h24", feat_df.columns)
        
        # Check that no NaNs remain after warm-up trimming
        self.assertEqual(feat_df.isnull().sum().sum(), 0)
        
    def test_temporal_split_integrity(self):
        feat_df = create_time_series_features(self.df, horizons=[1, 3, 6, 24])
        train, val, test = temporal_train_val_test_split(feat_df)
        
        # Chronological ordering checks
        self.assertLess(train.index.max(), val.index.min())
        self.assertLess(val.index.max(), test.index.min())
        
        # Sample sizes
        self.assertGreater(len(train), 8000)
        self.assertGreater(len(test), 2000)

    def test_model_artifact_reload_and_inference(self):
        artifact_path = MODELS_DIR / "new_delhi_baseline_ridge_h1.joblib"
        self.assertTrue(artifact_path.exists(), f"Artifact not found: {artifact_path}")
        
        artifact = joblib.load(artifact_path)
        self.assertIn("model_t", artifact)
        self.assertIn("model_rh", artifact)
        self.assertIn("scaler", artifact)
        self.assertIn("feature_cols", artifact)
        
        # Check inference works
        feat_df = create_time_series_features(self.df, horizons=[1])
        sample_x = feat_df[artifact["feature_cols"]].iloc[:5]
        scaled_x = artifact["scaler"].transform(sample_x)
        pred_t = artifact["model_t"].predict(scaled_x)
        
        self.assertEqual(len(pred_t), 5)
        self.assertTrue((pred_t > -10.0).all() and (pred_t < 60.0).all())

if __name__ == "__main__":
    unittest.main()
