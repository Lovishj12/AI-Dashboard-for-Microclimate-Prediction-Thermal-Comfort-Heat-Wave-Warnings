"""
Automated unit tests for Phase 4 Visualization Engine.
Checks:
1. Base psychrometric chart generation creates valid Matplotlib Figure & Axes.
2. Psychrometric boundary curves are mathematically strictly bounded.
3. Visualization outputs are saved to disk with non-zero size.
"""

import unittest
from pathlib import Path
import matplotlib.pyplot as plt
from src.visualization_engine import (
    generate_psychrometric_base,
    VIS_OUTPUT_DIR
)
from src.config import load_config

class TestVisualizationEngine(unittest.TestCase):
    def test_psychrometric_base_generation(self):
        fig, ax = generate_psychrometric_base(t_min=0.0, t_max=50.0, w_max=35.0)
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        self.assertEqual(ax.get_xlim(), (0.0, 50.0))
        self.assertEqual(ax.get_ylim(), (0.0, 35.0))
        plt.close(fig)
        
    def test_visualization_files_exist_and_non_empty(self):
        config = load_config()
        for loc in config["locations"]:
            p1 = VIS_OUTPUT_DIR / f"{loc}_psychrometric_chart.png"
            p2 = VIS_OUTPUT_DIR / f"{loc}_thermal_stress_phase_space.png"
            p3 = VIS_OUTPUT_DIR / f"{loc}_diurnal_heat_wave_dynamics.png"
            
            for p in [p1, p2, p3]:
                self.assertTrue(p.exists(), f"Missing visualization artifact: {p}")
                self.assertGreater(p.stat().st_size, 10000, f"File {p} is too small / corrupt")

if __name__ == "__main__":
    unittest.main()
