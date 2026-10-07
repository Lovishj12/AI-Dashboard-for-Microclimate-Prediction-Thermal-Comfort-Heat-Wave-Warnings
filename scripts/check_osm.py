import urllib.request
import urllib.parse
import json

bbox = "22.308,87.300,22.324,87.322"
query = f"""[out:json][timeout:30];
(
  way["building"]["name"]({bbox});
  relation["building"]["name"]({bbox});
);
out tags center 50;"""

url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(query)
req = urllib.request.Request(url, headers={"User-Agent": "BTP-IITKGP-Microclimate/1.0"})

try:
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
        elements = data.get("elements", [])
        print(f"Total named buildings found: {len(elements)}")
        for e in elements[:12]:
            tags = e.get("tags", {})
            center = e.get("center", {})
            print(f"- {tags.get('name')}: lat={center.get('lat')}, lon={center.get('lon')}, type={tags.get('building')}")
except Exception as err:
    print(f"Error querying Overpass: {err}")
