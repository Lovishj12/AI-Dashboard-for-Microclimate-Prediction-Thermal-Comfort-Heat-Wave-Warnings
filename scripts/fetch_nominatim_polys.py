import urllib.request
import urllib.parse
import json
import time

landmarks = [
    {"id": "main_building", "q": "Main Building IIT Kharagpur"},
    {"id": "nalanda_complex", "q": "Nalanda Classroom Complex IIT Kharagpur"},
    {"id": "takshashila_complex", "q": "Takshashila Complex Kharagpur"},
    {"id": "kalidas_auditorium", "q": "Kalidas Auditorium Kharagpur"},
    {"id": "central_library", "q": "Central Library IIT Kharagpur"},
    {"id": "cse_department", "q": "Computer Science IIT Kharagpur"},
    {"id": "electrical_engineering", "q": "Electrical Engineering IIT Kharagpur"},
    {"id": "mechanical_engineering", "q": "Mechanical Engineering IIT Kharagpur"},
    {"id": "technology_guest_house", "q": "Technology Guest House Kharagpur"},
    {"id": "tata_sports_complex", "q": "TATA Sports Complex Kharagpur"},
    {"id": "jnan_ghosh_stadium", "q": "Jnan Ghosh Stadium Kharagpur"},
    {"id": "bc_roy_hospital", "q": "B. C. Roy Technology Hospital Kharagpur"},
    {"id": "nehru_hall", "q": "Nehru Hall of Residence Kharagpur"},
    {"id": "patel_hall", "q": "Patel Hall of Residence Kharagpur"},
    {"id": "azad_hall", "q": "Azad Hall of Residence Kharagpur"},
    {"id": "rp_hall", "q": "Rajendra Prasad Hall of Residence Kharagpur"},
    {"id": "rk_hall", "q": "Radhakrishnan Hall of Residence Kharagpur"},
]

out = {}
for item in landmarks:
    url = "https://nominatim.openstreetmap.org/search?q=" + urllib.parse.quote(item["q"]) + "&format=json&polygon_geojson=1&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": "BTP-IIT-KGP-Research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            if res and "geojson" in res[0]:
                geom = res[0]["geojson"]
                print(f"Found {item['id']}: {geom['type']} with {len(geom.get('coordinates', []))} coords")
                out[item["id"]] = geom
            else:
                print(f"No polygon for {item['id']}")
    except Exception as e:
        print(f"Error {item['id']}: {e}")
    time.sleep(1.1)

with open("data/nominatim_polygons.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print("Saved nominatim_polygons.json")
