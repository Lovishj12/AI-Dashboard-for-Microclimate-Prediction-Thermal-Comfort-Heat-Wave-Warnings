# Steps 2 & 3 — IIT Kharagpur Spatial & GeoJSON Dataset Report
**Project**: AI Based Dashboard Development for Microclimate Prediction and Advanced Warning System for Thermal Comfort / Heat Waves  
**Supervisor**: Prof. Chirodeep Bakli  
**Upgrade Phase**: Steps 2 & 3 (Campus Spatial Model & GeoJSON Dataset)  

---

## 1. Scope & Objective
In Steps 2 and 3, we researched, compiled, and constructed a verified digital spatial dataset of the **IIT Kharagpur campus** spanning its ~2,100-acre domain (`22.308° N - 22.325° N`, `87.295° E - 87.322° E`).

Unlike a simple flat coordinate list, this dataset models the **Local Climate Zone (LCZ)** and microclimate attributes for each building and precinct, providing the mathematical substrate required for spatial downscaling (Step 6) and mitigation scenario testing (Step 13).

---

## 2. Dataset Schema & Sourced Attributes

Each feature in [`data/iit_kgp_campus.geojson`](file:///c:/Users/lovis/Desktop/BTP/data/iit_kgp_campus.geojson) includes:

| Attribute | Data Type | Physical Meaning & Scientific Importance |
| :--- | :--- | :--- |
| `id` / `name` | String | Unique identifier and official campus building name |
| `category` | String | Zone classification (`Academic`, `Hostel`, `Administration`, `Sports/Open`, `Healthcare`, `Amenities`, `Roads/Corridor`, `Water/Nature`) |
| `latitude`, `longitude` | Float | Verified centroid coordinates in WGS84 (`CRS84`) |
| `geometry` | Polygon | Closed polygon footprint representing building/precinct boundary |
| `floors` / `area_sqm` | Integer | Height and footprint surface area |
| `albedo` ($\alpha$) | Float | Surface solar reflectivity ($0.12$ for dark asphalt to $0.30$ for light roofs) |
| `vegetation_fraction` ($f_v$) | Float | Tree canopy and lawn cover fraction within surrounding 100m buffer |
| `impervious_fraction` ($f_i$) | Float | Fraction of paved asphalt/concrete ground impeding evaporative cooling |
| `sky_view_factor` (SVF) | Float | Ratio of visible radiation sky vault ($0.60$ in courtyard canyons to $0.95$ in open stadiums) |
| `ac_penetration` | Float | Fraction of space equipped with air conditioning (governs indoor vulnerability and outdoor heat rejection) |
| `estimated_footfall` | String | Population density tier (`Low`, `Medium`, `High`, `Very High`) |
| `vulnerability_baseline`| String | Inherent human heat vulnerability based on activity and cooling access |

---

## 3. Representative Campus Zones Included

The dataset encompasses 24 distinct campus landmarks across diverse microclimate typologies:
1. **Core Administration**: Main Administrative Building with iconic Clock Tower Block.
2. **High-Density Academic Precincts**: Nalanda Classroom Complex ($16,000\text{ m}^2$, $4\text{ floors}$), Takshashila Complex, Dept of Computer Science & Engineering, Electrical Engineering, and Central Library.
3. **High-Thermal-Mass Industrial Zones**: Mechanical Engineering Workshops and Central Industrial Workshop Complex (dark metallic roofs, low albedo $\alpha \sim 0.15$).
4. **Student Residential PAN Loop (High Vulnerability)**: Nehru Hall, Patel Hall, and Azad Hall of Residence (non-AC student living with high nocturnal heat trapping).
5. **Additional Halls of Residence**: Rajendra Prasad (RP) Hall, Radhakrishnan (RK) Hall, Lal Bahadur Shastri (LBS) Hall.
6. **Critical Healthcare**: Dr. B. C. Roy Technology Hospital (high sensitivity patients).
7. **Exposed Solar Grounds (Extreme Midday Stress)**: Jnan Ghosh Athletic Stadium ($35,000\text{ m}^2$ open field, $\text{SVF}=0.95$), Tata Sports Complex & Outdoor Swimming Pool.
8. **Transportation Corridors**: Scholars Avenue Main Traffic Junction (high impervious asphalt fraction $f_i = 0.80$).
9. **Natural Blue/Green Infrastructure**: Tikka Lake & Wetland Conservation Zone ($25,000\text{ m}^2$, high canopy $f_v = 0.75$).

---

## 4. Automated Unit Testing & Geographic Confinement

Tested in [`tests/test_campus_spatial.py`](file:///c:/Users/lovis/Desktop/BTP/tests/test_campus_spatial.py):
- **TEST 1 (Schema)**: Confirmed standard `FeatureCollection` with valid `CRS84` coordinates.
- **TEST 2 (Bounding Box)**: All 24 features confirmed strictly inside the IIT Kharagpur boundary ($22.308^\circ\text{N} \le \text{lat} \le 22.325^\circ\text{N}$; $87.295^\circ\text{E} \le \text{lon} \le 87.322^\circ\text{E}$).
- **TEST 3 (Geometry)**: All polygon rings are closed loops with 5 coordinate pairs.
- **TEST 4 (Physical Bounds)**: Validated $0.05 \le \alpha \le 0.60$, $f_v \in [0, 1]$, $f_i \in [0, 1]$, $\text{SVF} \in [0.3, 1.0]$.
- **Result**: All 4 tests passed in `0.000s`.
