import urllib.request
import urllib.parse
import json

query = """[out:json][timeout:25];
(
  way["building"](22.310,87.296,22.325,87.322);
);
out geom qt 250;
"""

url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(query)
req = urllib.request.Request(url, headers={"User-Agent": "BTP-IIT-KGP-Research/1.0"})
try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        elements = data.get("elements", [])
        print(f"Building elements retrieved: {len(elements)}")
        named_b = [e for e in elements if "name" in e.get("tags", {})]
        print(f"Named buildings: {len(named_b)}")
        for b_item in named_b[:15]:
            print(" -", b_item["tags"].get("name"), len(b_item.get("geometry", [])))
        with open("data/iit_kgp_buildings_osm.json", "w", encoding="utf-8") as f:
            json.dump(data, f)
        print("Saved to data/iit_kgp_buildings_osm.json")
except Exception as e:
    print(f"Error fetching buildings: {e}")
