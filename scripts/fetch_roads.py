import urllib.request
import urllib.parse
import json

query = """[out:json][timeout:20];
(
  way["highway"](22.311,87.296,22.324,87.322);
);
out geom qt 100;
"""

url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(query)
req = urllib.request.Request(url, headers={"User-Agent": "BTP-IIT-KGP-Research/1.0"})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode())
        elements = data.get("elements", [])
        print(f"Road elements retrieved: {len(elements)}")
        named_roads = [e for e in elements if "name" in e.get("tags", {})]
        print(f"Named roads: {len(named_roads)}")
        for r_item in named_roads[:10]:
            print(" -", r_item["tags"].get("name"), len(r_item.get("geometry", [])))
        with open("data/iit_kgp_roads_osm.json", "w", encoding="utf-8") as f:
            json.dump(data, f)
        print("Saved to data/iit_kgp_roads_osm.json")
except Exception as e:
    print(f"Error fetching roads: {e}")
