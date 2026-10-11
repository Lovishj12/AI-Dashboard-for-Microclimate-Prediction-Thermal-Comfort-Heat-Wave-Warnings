import urllib.request
import urllib.parse
import json

endpoints = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter"
]

query = """[out:json][timeout:20];
(
  way["building"](22.312,87.300,22.324,87.318);
  way["highway"~"primary|secondary|tertiary|residential|service"](22.312,87.300,22.324,87.318);
);
out body geom qt 300;
"""

success = False
for ep in endpoints:
    url = ep + "?data=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={"User-Agent": "IIT-KGP-BTP-Microclimate/1.0"})
    try:
        print(f"Trying {ep}...")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elements = data.get("elements", [])
            print(f"Success! Total OSM elements retrieved: {len(elements)}")
            buildings = [e for e in elements if "building" in e.get("tags", {})]
            roads = [e for e in elements if "highway" in e.get("tags", {})]
            print(f"Buildings: {len(buildings)}, Roads: {len(roads)}")
            with open("data/raw_osm_kgp.json", "w", encoding="utf-8") as f:
                json.dump(data, f)
            print("Saved raw OSM data to data/raw_osm_kgp.json")
            success = True
            break
    except Exception as e:
        print(f"Failed {ep}: {e}")

if not success:
    print("Could not retrieve live OSM from endpoints.")

