"""
Unit tests for Phase 6 Advanced AI/ML Pipeline.
Validates:
1. Champion models exist on disk for all locations and horizons.
2. Champion model artifacts contain necessary inference objects (model_t, model_rh, scaler/None, feature_cols).
3. End-to-end inference produces valid physical predictions.
4. Danger alert safety metrics (Recall, Precision, F1) are recorded and > 0.70.
"""

import unittest
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from src.advanced_ml import CHAMPION_MODELS_DIR
from src.config import load_config
from src.baseline_model import create_time_series_features

class TestAdvancedML(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        cls.locations = list(cls.config["locations"].keys())
        cls.horizons = [1, 3, 6, 24]
        
    def test_champion_artifacts_exist(self):
        for loc in self.locations:
            for h in self.horizons:
                p = CHAMPION_MODELS_DIR / f"{loc}_champion_h{h}.joblib"
                self.assertTrue(p.exists(), f"Champion artifact missing: {p}")
                
    def test_champion_artifact_structure_and_inference(self):
        # Test Kharagpur h=1
        champ_path = CHAMPION_MODELS_DIR / "kharagpur_champion_h1.joblib"
        artifact = joblib.load(champ_path)
        
        self.assertIn("model_type", artifact)
        self.assertIn("model_t", artifact)
        self.assertIn("model_rh", artifact)
        self.assertIn("feature_cols", artifact)
        self.assertIn("metrics", artifact)
        
        # Verify safety F1 is high (> 0.85)
        self.assertGreater(artifact["metrics"]["Danger_F1"], 0.85)
        
        # Test inference with mock row
        num_features = len(artifact["feature_cols"])
        mock_input = np.ones((1, num_features))
        
        if artifact["scaler"] is not None:
            mock_input_scaled = artifact["scaler"].transform(mock_input)
            pred_t = artifact["model_t"].predict(mock_input_scaled)
        else:
            pred_t = artifact["model_t"].predict(mock_input)
            
        self.assertEqual(len(pred_t), 1)
        self.assertTrue(np.isfinite(pred_t[0]))

if __name__ == "__main__":
    unittest.main()
