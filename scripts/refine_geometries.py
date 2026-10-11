import json
import math

with open('data/iit_kgp_campus.geojson', 'r', encoding='utf-8') as f:
    d = json.load(f)

def make_building_geometry(lat, lon, length_m, width_m, style='rectangle', orientation_deg=0):
    d_lat_m = 1.0 / 111000.0
    d_lon_m = 1.0 / 102700.0
    
    rad = math.radians(orientation_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    
    def rotate_pt(x, y):
        rx = x * cos_a - y * sin_a
        ry = x * sin_a + y * cos_a
        return [round(lon + rx * d_lon_m, 6), round(lat + ry * d_lat_m, 6)]
        
    pts = []
    hl = length_m / 2.0
    hw = width_m / 2.0
    
    if style == 'h_shaped': # Classic academic/library wing layout
        c_hw = hw * 0.35
        pts = [
            rotate_pt(-hl, -hw),
            rotate_pt(-hl * 0.45, -hw),
            rotate_pt(-hl * 0.45, -c_hw),
            rotate_pt(hl * 0.45, -c_hw),
            rotate_pt(hl * 0.45, -hw),
            rotate_pt(hl, -hw),
            rotate_pt(hl, hw),
            rotate_pt(hl * 0.45, hw),
            rotate_pt(hl * 0.45, c_hw),
            rotate_pt(-hl * 0.45, c_hw),
            rotate_pt(-hl * 0.45, hw),
            rotate_pt(-hl, hw),
            rotate_pt(-hl, -hw)
        ]
    elif style == 'u_shaped': # Nalanda, complexes with courtyard
        pts = [
            rotate_pt(-hl, -hw),
            rotate_pt(hl, -hw),
            rotate_pt(hl, hw),
            rotate_pt(hl * 0.4, hw),
            rotate_pt(hl * 0.4, -hw * 0.3),
            rotate_pt(-hl * 0.4, -hw * 0.3),
            rotate_pt(-hl * 0.4, hw),
            rotate_pt(-hl, hw),
            rotate_pt(-hl, -hw)
        ]
    elif style == 'stepped_facets': # Auditorium, octagonal pavilion
        pts = [
            rotate_pt(-hl * 0.7, -hw),
            rotate_pt(hl * 0.7, -hw),
            rotate_pt(hl, -hw * 0.6),
            rotate_pt(hl, hw * 0.6),
            rotate_pt(hl * 0.7, hw),
            rotate_pt(-hl * 0.7, hw),
            rotate_pt(-hl, hw * 0.6),
            rotate_pt(-hl, -hw * 0.6),
            rotate_pt(-hl * 0.7, -hw)
        ]
    elif style == 'lake_waterbody': # Tikka Lake organic boundary
        for deg in range(0, 360, 20):
            r_rad = math.radians(deg)
            wobble = 1.0 + 0.12 * math.sin(2 * r_rad) + 0.08 * math.cos(3 * r_rad)
            px = round(lon + (hl * math.cos(r_rad) * wobble) * d_lon_m, 6)
            py = round(lat + (hw * math.sin(r_rad) * wobble) * d_lat_m, 6)
            pts.append([px, py])
        pts.append(pts[0])
    elif style == 'linear_spine': # Sports complex / road corridor
        pts = [
            rotate_pt(-hl, -hw),
            rotate_pt(hl, -hw),
            rotate_pt(hl, hw),
            rotate_pt(-hl, hw),
            rotate_pt(-hl, -hw)
        ]
    else: # L-shaped default for academic departments
        pts = [
            rotate_pt(-hl, -hw),
            rotate_pt(hl, -hw),
            rotate_pt(hl, hw * 0.25),
            rotate_pt(hl * 0.15, hw * 0.25),
            rotate_pt(hl * 0.15, hw),
            rotate_pt(-hl, hw),
            rotate_pt(-hl, -hw)
        ]
    return pts

refinements = {
    'nalanda_complex': {'l': 130, 'w': 90, 'style': 'u_shaped', 'deg': -12},
    'central_library': {'l': 90, 'w': 70, 'style': 'h_shaped', 'deg': 5},
    'cse_department': {'l': 80, 'w': 55, 'style': 'l_shaped', 'deg': 10},
    'electrical_engineering': {'l': 85, 'w': 60, 'style': 'h_shaped', 'deg': -5},
    'mechanical_engineering': {'l': 105, 'w': 75, 'style': 'h_shaped', 'deg': 8},
    'kalidas_auditorium': {'l': 70, 'w': 50, 'style': 'stepped_facets', 'deg': 0},
    'gymkhana': {'l': 65, 'w': 48, 'style': 'stepped_facets', 'deg': 15},
    'central_workshop': {'l': 100, 'w': 65, 'style': 'h_shaped', 'deg': -8},
    'tikka_lake_zone': {'l': 160, 'w': 100, 'style': 'lake_waterbody', 'deg': 25},
    'tata_sports_complex': {'l': 120, 'w': 80, 'style': 'linear_spine', 'deg': 0},
    'old_sac_grounds': {'l': 75, 'w': 60, 'style': 'stepped_facets', 'deg': 10},
    'step_complex': {'l': 80, 'w': 55, 'style': 'l_shaped', 'deg': -10},
    'scholars_avenue_junction': {'l': 110, 'w': 35, 'style': 'linear_spine', 'deg': 18},
}

for feat in d['features']:
    f_id = feat['properties']['id']
    if f_id in refinements:
        r = refinements[f_id]
        lat = feat['properties']['latitude']
        lon = feat['properties']['longitude']
        new_pts = make_building_geometry(lat, lon, r['l'], r['w'], r['style'], r['deg'])
        feat['geometry'] = {'type': 'Polygon', 'coordinates': [new_pts]}
        print(f"Refined {f_id} to style {r['style']} ({len(new_pts)} vertices)")

with open('data/iit_kgp_campus.geojson', 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2)
print("Saved data/iit_kgp_campus.geojson successfully")
