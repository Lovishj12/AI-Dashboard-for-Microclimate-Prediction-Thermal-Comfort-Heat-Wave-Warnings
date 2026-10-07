import urllib.request
import urllib.parse
import json

query = """[out:json][timeout:25];
(
  node["amenity"="university"](22.30,87.29,22.33,87.33);
  way["building"]["name"](22.310,87.295,22.325,87.320);
);
out center tags 30;"""

url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(query)
req = urllib.request.Request(url, headers={"User-Agent": "BTP-Research/1.0"})

try:
    with urllib.request.urlopen(req, timeout=25) as res:
        data = json.loads(res.read().decode("utf-8"))
        elements = data.get("elements", [])
        print(f"Elements: {len(elements)}")
        for e in elements[:15]:
            t = e.get("tags", {})
            c = e.get("center", {})
            lat = c.get("lat") or e.get("lat")
            lon = c.get("lon") or e.get("lon")
            print(f"- {t.get('name')}: ({lat}, {lon})")
except Exception as e:
    print(f"Error: {e}")
