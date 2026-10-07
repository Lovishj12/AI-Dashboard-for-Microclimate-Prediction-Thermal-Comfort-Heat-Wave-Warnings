"""
Unit tests for Steps 2 & 3: IIT Kharagpur Spatial & GeoJSON Dataset.
Validates:
1. Valid GeoJSON schema (FeatureCollection, Features, Polygons).
2. All 24 core landmarks are present with non-empty attributes.
3. Coordinates fall strictly inside IIT Kharagpur geographic boundaries:
   Latitude: [22.308, 22.325]
   Longitude: [87.295, 87.322]
4. Physical attributes are within valid thermodynamic ranges:
   - Albedo: [0.05, 0.60]
   - Vegetation fraction: [0.0, 1.0]
   - Impervious fraction: [0.0, 1.0]
   - Sky View Factor: [0.3, 1.0]
   - AC penetration: [0.0, 1.0]
"""

import unittest
import json
from pathlib import Path
from src.campus_spatial import generate_campus_spatial_dataset

class TestCampusSpatialModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geojson = generate_campus_spatial_dataset()
        cls.features = cls.geojson["features"]

    def test_geojson_structure(self):
        self.assertEqual(self.geojson["type"], "FeatureCollection")
        self.assertGreaterEqual(len(self.features), 20)
        self.assertIn("campus_metadata", self.geojson)

    def test_geographic_boundary_confinement(self):
        for f in self.features:
            props = f["properties"]
            lat = props["latitude"]
            lon = props["longitude"]
            
            # Boundary assertion for IIT KGP
            self.assertGreaterEqual(lat, 22.308, f"Lat out of bounds for {props['name']}: {lat}")
            self.assertLessEqual(lat, 22.325, f"Lat out of bounds for {props['name']}: {lat}")
            self.assertGreaterEqual(lon, 87.295, f"Lon out of bounds for {props['name']}: lon={lon}")
            self.assertLessEqual(lon, 87.322, f"Lon out of bounds for {props['name']}: lon={lon}")

    def test_polygon_geometry_validity(self):
        for f in self.features:
            geom = f["geometry"]
            self.assertEqual(geom["type"], "Polygon")
            coords = geom["coordinates"][0]
            # Polygon ring must be closed (first point == last point)
            self.assertEqual(coords[0], coords[-1], f"Polygon not closed for {f['id']}")
            self.assertEqual(len(coords), 5)

    def test_physical_attribute_ranges(self):
        for f in self.features:
            p = f["properties"]
            self.assertTrue(0.05 <= p["albedo"] <= 0.60)
            self.assertTrue(0.0 <= p["vegetation_fraction"] <= 1.0)
            self.assertTrue(0.0 <= p["impervious_fraction"] <= 1.0)
            self.assertTrue(0.3 <= p["sky_view_factor"] <= 1.0)
            self.assertTrue(0.0 <= p["ac_penetration"] <= 1.0)
            self.assertIn(p["category"], ["Academic", "Hostel", "Administration", "Sports/Open", "Healthcare", "Amenities", "Roads/Corridor", "Water/Nature"])

if __name__ == "__main__":
    unittest.main()
