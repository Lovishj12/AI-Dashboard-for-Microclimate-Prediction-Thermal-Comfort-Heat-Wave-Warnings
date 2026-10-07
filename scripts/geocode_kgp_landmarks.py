import urllib.request
import urllib.parse
import json
import time

headers = {'User-Agent': 'BTP-Research-KGP/1.0'}
viewbox = '87.295,22.328,87.325,22.305'
queries = [
    'Rajendra Prasad Hall', 'Radhakrishnan Hall', 'Nehru Hall', 'Patel Hall', 'Azad Hall',
    'Lal Bahadur Shastri Hall', 'Megalite Hall', 'Homi J Bhabha Hall', 'B. R. Ambedkar Hall',
    'Main Building', 'Nalanda', 'Vikramshila', 'Takshashila', 'Kalidas Auditorium',
    'Technology Guest House', 'Tata Sports Complex', 'Jnan Ghosh Stadium', 'Technology Students Gymkhana',
    'B. C. Roy Technology Hospital', 'STEP', 'Central Library', 'Civil Engineering',
    'Computer Science', 'Electrical Engineering', 'Mechanical Engineering'
]

found = []
for q in queries:
    time.sleep(0.8) # Nominatim 1 req/sec policy
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q + ' Kharagpur')}&format=json&limit=1"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read().decode())
            if res:
                lat = float(res[0]['lat'])
                lon = float(res[0]['lon'])
                name = res[0]['display_name']
                # Check if coordinates fall in Kharagpur bounds
                if 22.30 <= lat <= 22.33 and 87.29 <= lon <= 87.33:
                    found.append({'query': q, 'lat': lat, 'lon': lon, 'display': name})
                    print(f"VERIFIED: {q} -> ({lat}, {lon})")
                else:
                    print(f"OUT OF BOUNDS: {q} -> ({lat}, {lon})")
            else:
                print(f"NOT FOUND: {q}")
    except Exception as e:
        print(f"ERR: {q} -> {e}")

print(f"\nTotal verified campus landmarks found: {len(found)}")
with open('data/kgp_verified_landmarks.json', 'w', encoding='utf-8') as f:
    json.dump(found, f, indent=2)
