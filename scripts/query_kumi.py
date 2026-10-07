import urllib.request
import urllib.parse
import json

query = """[out:json][timeout:25];
(
  way["name"]["building"](22.31,87.29,22.33,87.33);
  relation["name"]["building"](22.31,87.29,22.33,87.33);
);
out center tags 40;"""

url = "https://overpass.kumi.systems/api/interpreter?data=" + urllib.parse.quote(query)
req = urllib.request.Request(url, headers={"User-Agent": "BTP-Research/1.0"})

try:
    with urllib.request.urlopen(req, timeout=25) as res:
        data = json.loads(res.read().decode("utf-8"))
        elements = data.get("elements", [])
        print(f"Elements from kumi mirror: {len(elements)}")
        for e in elements[:20]:
            t = e.get("tags", {})
            c = e.get("center", {})
            lat = c.get("lat") or e.get("lat")
            lon = c.get("lon") or e.get("lon")
            print(f"- {t.get('name')}: ({lat}, {lon}) [type: {t.get('building')}]")
except Exception as err:
    print(f"Error: {err}")
