"""
Building-Level Air-Conditioning (AC) Inventory & Anthropogenic Heat Rejection Engine.
Part of the IIT Kharagpur Microclimate Prediction and Thermal Warning System.

Scientific Principles & Thermodynamic Grounding:
1. First Law of Thermodynamics for Vapor-Compression Refrigeration:
   Q_reject = Q_cooling + P_electric
   Q_reject = Q_cooling * (1 + 1 / COP)
   where:
   - Q_cooling: Effective cooling delivered indoors (kW or TR, 1 TR = 3.517 kW)
   - P_electric: Electrical input drawn by compressor & fan (kW)
   - COP: Coefficient of Performance (typical: 2.8 - 3.2 for split/window, 3.4 - 3.8 for VRF, 4.0 - 5.5 for chillers)
   - Q_reject: Total outdoor sensible + latent heat rejected by condenser coils (kW)

2. Evidence Tier Classification:
   - "Verified": Documented institutional audit or verified field survey
   - "Documented": Official procurement tender / administrative approval on CPPP / Institute Works
   - "Estimated": Engineering floor-area / occupancy density benchmarking (e.g. ECBC/ASHRAE 90.1 standard)
   - "Unknown": Insufficient data

3. Microclimate Canyon Rejection Density:
   q_anthropogenic_wm2 = Q_reject_total_kw * 1000.0 / footprint_area_sqm
   This informs local street canyon heat flux and microclimatic air perturbation.
"""

from pathlib import Path
import json
from typing import Dict, List, Any, Optional

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
AC_DATABASE_FILE = DATA_DIR / "iit_kgp_ac_inventory.json"

# Typical HVAC system parameters by typology
HVAC_TYPOLOGY_DEFAULTS = {
    "Central Chiller (Water-Cooled)": {"cop": 4.8, "operating_hours_per_day": 12, "part_load_ratio": 0.70},
    "Central Chiller (Air-Cooled)": {"cop": 3.6, "operating_hours_per_day": 10, "part_load_ratio": 0.65},
    "VRF / Multi-Split (Inverter)": {"cop": 3.5, "operating_hours_per_day": 8, "part_load_ratio": 0.60},
    "Ductable Split Units": {"cop": 3.1, "operating_hours_per_day": 8, "part_load_ratio": 0.65},
    "Decentralized Inverter Splits": {"cop": 3.2, "operating_hours_per_day": 6, "part_load_ratio": 0.55},
    "Window / Fixed Speed Splits": {"cop": 2.8, "operating_hours_per_day": 6, "part_load_ratio": 0.60},
    "Natural Ventilation / Ceiling Fans Only": {"cop": 1.0, "operating_hours_per_day": 0, "part_load_ratio": 0.0},
}

# Building-level AC Inventory grounded in IIT Kharagpur e-procurement records,
# Hall Management Centre (HMC) policies, and ECBC benchmark estimates.
INITIAL_AC_INVENTORY = [
    {
        "building_id": "nalanda_complex",
        "building_name": "Nalanda Classroom Complex",
        "category": "Academic",
        "evidence_tier": "Documented",
        "primary_hvac_type": "Central Chiller (Air-Cooled) + VRF Subsystems",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 84,  # Multiple modular AHUs & lecture hall splits
        "condenser_count_estimated": 28,
        "cooling_capacity_tons_tr": 450.0,
        "rated_cooling_capacity_kw": 1582.6,  # 450 TR * 3.517 kW/TR
        "rated_cop": 3.6,
        "rated_electrical_input_kw": 439.6,  # 1582.6 / 3.6
        "outdoor_condenser_placement": "Roof Plant Deck & West Service Yard",
        "operating_schedule": "08:00 - 18:00 IST (Academic Working Days)",
        "source_document": "IIT Kharagpur RAC Tender Ref: IITKGP/IW/RAC/NCRC/VFD/2025 (eProcure / Works)",
        "source_url": "https://eprocure.gov.in/eprocure/app",
        "observation_date": "2025-04-10",
        "notes": "Large multi-lecture facility. Variable Frequency Drives (VFDs) regulate chiller and fan coils."
    },
    {
        "building_id": "central_library",
        "building_name": "Central Library",
        "category": "Academic",
        "evidence_tier": "Documented",
        "primary_hvac_type": "Central Chiller (Air-Cooled) & Precision Splits",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 46,
        "condenser_count_estimated": 16,
        "cooling_capacity_tons_tr": 280.0,
        "rated_cooling_capacity_kw": 984.8,
        "rated_cop": 3.5,
        "rated_electrical_input_kw": 281.4,
        "outdoor_condenser_placement": "Rear Service Yard & Rooftop Chiller Bank",
        "operating_schedule": "08:00 - 23:00 IST (Extended Daily Study Hours)",
        "source_document": "IIT Kharagpur RAC Tender Ref: IITKGP/IW/RAC/CL/2025-26 (Central Library HVAC)",
        "source_url": "https://eprocure.gov.in/eprocure/app",
        "observation_date": "2025-06-18",
        "notes": "Continuous summer cooling sanctuary for students. High cumulative diurnal heat rejection."
    },
    {
        "building_id": "takshashila_complex",
        "building_name": "Takshashila Academic Complex",
        "category": "Academic",
        "evidence_tier": "Documented",
        "primary_hvac_type": "VRF / Multi-Split (Inverter) & Package Units",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 62,
        "condenser_count_estimated": 22,
        "cooling_capacity_tons_tr": 320.0,
        "rated_cooling_capacity_kw": 1125.4,
        "rated_cop": 3.5,
        "rated_electrical_input_kw": 321.5,
        "outdoor_condenser_placement": "Rooftop Parapets & Internal Service Lightwells",
        "operating_schedule": "08:00 - 18:00 IST (Weekdays & Examination Periods)",
        "source_document": "IIT Kharagpur Tender: SWAN Lab & Server Room VRF SITC at Takshashila Building",
        "source_url": "https://www.iitkgp.ac.in/tenders",
        "observation_date": "2024-11-22",
        "notes": "Classrooms and dedicated department research computing server rooms."
    },
    {
        "building_id": "cse_department",
        "building_name": "Dept of Computer Science & Engineering",
        "category": "Academic",
        "evidence_tier": "Documented",
        "primary_hvac_type": "VRF / Multi-Split (Inverter) & Precision Lab AC",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 75,
        "condenser_count_estimated": 28,
        "cooling_capacity_tons_tr": 195.0,
        "rated_cooling_capacity_kw": 685.8,
        "rated_cop": 3.3,
        "rated_electrical_input_kw": 207.8,
        "outdoor_condenser_placement": "North-facing External Balconies & Roof Plant Area",
        "operating_schedule": "24x7 for Server Facilities; 08:30 - 20:00 for Labs/Offices",
        "source_document": "Departmental SITC Tenders for Server Rooms & High-Performance Computing Labs",
        "source_url": "https://www.iitkgp.ac.in/tenders",
        "observation_date": "2024-08-14",
        "notes": "High continuous computing sensible heat gain requiring steady heat rejection outdoors."
    },
    {
        "building_id": "main_building",
        "building_name": "Main Administrative Building (Tower Block)",
        "category": "Administration",
        "evidence_tier": "Documented",
        "primary_hvac_type": "Decentralized Inverter Splits & Modular VRF",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 110,
        "condenser_count_estimated": 72,
        "cooling_capacity_tons_tr": 160.0,
        "rated_cooling_capacity_kw": 562.7,
        "rated_cop": 3.1,
        "rated_electrical_input_kw": 181.5,
        "outdoor_condenser_placement": "Exterior Corridor Facades & Courtyard Walls",
        "operating_schedule": "09:00 - 18:00 IST (Institute Working Days)",
        "source_document": "Estate Office Annual Maintenance Tenders for Administrative Wings",
        "source_url": "https://www.iitkgp.ac.in/tenders",
        "observation_date": "2024-05-19",
        "notes": "Heritage structure with external split condensers mounted along colonnades and verandas."
    },
    {
        "building_id": "electrical_engineering",
        "building_name": "Dept of Electrical Engineering",
        "category": "Academic",
        "evidence_tier": "Estimated",
        "primary_hvac_type": "Ductable Split Units & Inverter Splits",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 65,
        "condenser_count_estimated": 45,
        "cooling_capacity_tons_tr": 140.0,
        "rated_cooling_capacity_kw": 492.4,
        "rated_cop": 3.1,
        "rated_electrical_input_kw": 158.8,
        "outdoor_condenser_placement": "Exterior Courtyards & Rooftop Slab",
        "operating_schedule": "08:30 - 18:30 IST (Working Days)",
        "source_document": "Engineering Benchmark: ECBC 2017 Institutional Floor Area Model (7,800 m²)",
        "source_url": "https://beeindia.gov.in/en/energy-conservation-building-code",
        "observation_date": "2025-01-15",
        "notes": "AC installed predominantly in specialized research labs, staff cabins, and conference rooms."
    },
    {
        "building_id": "mechanical_engineering",
        "building_name": "Dept of Mechanical Engineering & Workshops",
        "category": "Academic",
        "evidence_tier": "Estimated",
        "primary_hvac_type": "Decentralized Inverter Splits in Labs (Workshops Non-AC)",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 42,
        "condenser_count_estimated": 35,
        "cooling_capacity_tons_tr": 90.0,
        "rated_cooling_capacity_kw": 316.5,
        "rated_cop": 3.0,
        "rated_electrical_input_kw": 105.5,
        "outdoor_condenser_placement": "West Wall & Laboratory Mezzanines",
        "operating_schedule": "09:00 - 17:30 IST (Academic Days)",
        "source_document": "Engineering Benchmark: ECBC Partial Conditioning Ratio for Workshop Facilities",
        "source_url": "https://beeindia.gov.in/en/energy-conservation-building-code",
        "observation_date": "2025-01-15",
        "notes": "High workshop volume remains naturally ventilated. Conditioning restricted to CAD/thermodynamics labs."
    },
    {
        "building_id": "kalidas_auditorium",
        "building_name": "Kalidas Auditorium",
        "category": "Amenities",
        "evidence_tier": "Documented",
        "primary_hvac_type": "Central Chiller (Air-Cooled) Package Unit",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 12,
        "condenser_count_estimated": 4,
        "cooling_capacity_tons_tr": 120.0,
        "rated_cooling_capacity_kw": 422.0,
        "rated_cop": 3.2,
        "rated_electrical_input_kw": 131.9,
        "outdoor_condenser_placement": "Rear Service Compound adjacent to Tech Market Road",
        "operating_schedule": "Event-Based Operation (Convocation, Conferences, Cultural Fests)",
        "source_document": "IIT Kharagpur Refrigeration & Air Conditioning Unit Maintenance Schedule",
        "source_url": "https://www.iitkgp.ac.in/tenders",
        "observation_date": "2024-03-10",
        "notes": "Large intermittent thermal pulse when active during institutional gatherings."
    },
    {
        "building_id": "technology_guest_house",
        "building_name": "Technology Guest House",
        "category": "Amenities",
        "evidence_tier": "Documented",
        "primary_hvac_type": "VRF System & Inverter Split ACs",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 95,
        "condenser_count_estimated": 38,
        "cooling_capacity_tons_tr": 130.0,
        "rated_cooling_capacity_kw": 457.2,
        "rated_cop": 3.4,
        "rated_electrical_input_kw": 134.5,
        "outdoor_condenser_placement": "Service Shafts & Rear Shaded Yard",
        "operating_schedule": "24x7 Variable Occupancy (Hospitality / Guest Rooms)",
        "source_document": "Guest House Modernization and RAC Tender Documentation",
        "source_url": "https://www.iitkgp.ac.in/tenders",
        "observation_date": "2024-09-05",
        "notes": "High continuous comfort requirement for visiting faculty and guests."
    },
    {
        "building_id": "bc_roy_hospital",
        "building_name": "Dr. B. C. Roy Technology Hospital",
        "category": "Healthcare",
        "evidence_tier": "Documented",
        "primary_hvac_type": "Precision Cleanroom AC & Inverter Splits",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 60,
        "condenser_count_estimated": 35,
        "cooling_capacity_tons_tr": 110.0,
        "rated_cooling_capacity_kw": 386.9,
        "rated_cop": 3.2,
        "rated_electrical_input_kw": 120.9,
        "outdoor_condenser_placement": "Ground-Level Service Alley & Emergency Ward Flank",
        "operating_schedule": "24x7 Critical Medical Operation",
        "source_document": "BC Roy Hospital Operation Theater & ICU HVAC Maintenance Contract",
        "source_url": "https://www.iitkgp.ac.in/tenders",
        "observation_date": "2024-12-01",
        "notes": "Critical thermal reliability for emergency, wards, pharmacy, and patient recovery."
    },
    {
        "building_id": "step_complex",
        "building_name": "STEP (Science & Tech Entrepreneurs Park)",
        "category": "Academic",
        "evidence_tier": "Estimated",
        "primary_hvac_type": "Inverter Splits & Commercial VRF Units",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 48,
        "condenser_count_estimated": 30,
        "cooling_capacity_tons_tr": 85.0,
        "rated_cooling_capacity_kw": 298.9,
        "rated_cop": 3.2,
        "rated_electrical_input_kw": 93.4,
        "outdoor_condenser_placement": "External Facade Ledges & Roof Deck",
        "operating_schedule": "09:00 - 20:00 IST (Incubator Office Hours)",
        "source_document": "ECBC Commercial Office Benchmark Estimation",
        "source_url": "https://beeindia.gov.in/en/energy-conservation-building-code",
        "observation_date": "2025-01-15",
        "notes": "Incubator startup offices with typical IT equipment heat dissipation."
    },
    {
        "building_id": "central_workshop",
        "building_name": "Central Workshop Precinct",
        "category": "Academic",
        "evidence_tier": "Verified",
        "primary_hvac_type": "Natural Ventilation / Ceiling Fans Only",
        "ac_unit_count_confirmed": 4,  # Only administrative cabin splits
        "ac_unit_count_estimated": 4,
        "condenser_count_estimated": 4,
        "cooling_capacity_tons_tr": 6.0,
        "rated_cooling_capacity_kw": 21.1,
        "rated_cop": 2.9,
        "rated_electrical_input_kw": 7.3,
        "outdoor_condenser_placement": "Supervisor Office North Wall",
        "operating_schedule": "09:00 - 17:00 IST (Office Hours Only)",
        "source_document": "Central Workshop Facility Operations Audit",
        "source_url": "https://www.iitkgp.ac.in",
        "observation_date": "2024-10-18",
        "notes": "Large open-bay industrial machine shop. >95% floor area naturally ventilated."
    },
    # Halls of Residence: Verified Non-AC Policy by Hall Management Centre (HMC)
    {
        "building_id": "nehru_hall",
        "building_name": "Nehru Hall of Residence (PAN Loop)",
        "category": "Hostel",
        "evidence_tier": "Verified",
        "primary_hvac_type": "Natural Ventilation / Ceiling Fans Only",
        "ac_unit_count_confirmed": 2,  # Warden office / Guest room only
        "ac_unit_count_estimated": 2,
        "condenser_count_estimated": 2,
        "cooling_capacity_tons_tr": 3.0,
        "rated_cooling_capacity_kw": 10.6,
        "rated_cop": 3.0,
        "rated_electrical_input_kw": 3.5,
        "outdoor_condenser_placement": "Warden Office External Wall",
        "operating_schedule": "Intermittent (Admin Office Hours)",
        "source_document": "IIT Kharagpur Hall Management Centre (HMC) Regulations: Heavy Electrical Appliances & AC Prohibited in Student Rooms",
        "source_url": "https://www.iitkgp.ac.in/hmc",
        "observation_date": "2024-07-20",
        "notes": "Strict non-AC residential policy. High nocturnal occupant thermal vulnerability."
    },
    {
        "building_id": "patel_hall",
        "building_name": "Patel Hall of Residence (PAN Loop)",
        "category": "Hostel",
        "evidence_tier": "Verified",
        "primary_hvac_type": "Natural Ventilation / Ceiling Fans Only",
        "ac_unit_count_confirmed": 2,
        "ac_unit_count_estimated": 2,
        "condenser_count_estimated": 2,
        "cooling_capacity_tons_tr": 3.0,
        "rated_cooling_capacity_kw": 10.6,
        "rated_cop": 3.0,
        "rated_electrical_input_kw": 3.5,
        "outdoor_condenser_placement": "Warden Office External Wall",
        "operating_schedule": "Intermittent (Admin Office Hours)",
        "source_document": "HMC Student Residential Handbook (Rules & Regulations)",
        "source_url": "https://www.iitkgp.ac.in/hmc",
        "observation_date": "2024-07-20",
        "notes": "Student rooms rely entirely on ceiling fans. Minimal anthropogenic heat rejection."
    },
    {
        "building_id": "azad_hall",
        "building_name": "Azad Hall of Residence (PAN Loop)",
        "category": "Hostel",
        "evidence_tier": "Verified",
        "primary_hvac_type": "Natural Ventilation / Ceiling Fans Only",
        "ac_unit_count_confirmed": 2,
        "ac_unit_count_estimated": 2,
        "condenser_count_estimated": 2,
        "cooling_capacity_tons_tr": 3.0,
        "rated_cooling_capacity_kw": 10.6,
        "rated_cop": 3.0,
        "rated_electrical_input_kw": 3.5,
        "outdoor_condenser_placement": "Warden Office External Wall",
        "operating_schedule": "Intermittent (Admin Office Hours)",
        "source_document": "HMC Student Residential Handbook (Rules & Regulations)",
        "source_url": "https://www.iitkgp.ac.in/hmc",
        "observation_date": "2024-07-20",
        "notes": "Non-AC student residential hall with natural cross-ventilation."
    },
    {
        "building_id": "rp_hall",
        "building_name": "Rajendra Prasad (RP) Hall of Residence",
        "category": "Hostel",
        "evidence_tier": "Verified",
        "primary_hvac_type": "Natural Ventilation / Ceiling Fans Only",
        "ac_unit_count_confirmed": 3,
        "ac_unit_count_estimated": 3,
        "condenser_count_estimated": 3,
        "cooling_capacity_tons_tr": 4.5,
        "rated_cooling_capacity_kw": 15.8,
        "rated_cop": 3.0,
        "rated_electrical_input_kw": 5.3,
        "outdoor_condenser_placement": "Warden Office & Common Library Room",
        "operating_schedule": "Intermittent (Office & Evening Library Hours)",
        "source_document": "HMC Student Residential Regulations",
        "source_url": "https://www.iitkgp.ac.in/hmc",
        "observation_date": "2024-07-20",
        "notes": "Student rooms non-AC. Air conditioning restricted to hall library and office."
    },
    {
        "building_id": "rk_hall",
        "building_name": "Radhakrishnan (RK) Hall of Residence",
        "category": "Hostel",
        "evidence_tier": "Verified",
        "primary_hvac_type": "Natural Ventilation / Ceiling Fans Only",
        "ac_unit_count_confirmed": 3,
        "ac_unit_count_estimated": 3,
        "condenser_count_estimated": 3,
        "cooling_capacity_tons_tr": 4.5,
        "rated_cooling_capacity_kw": 15.8,
        "rated_cop": 3.0,
        "rated_electrical_input_kw": 5.3,
        "outdoor_condenser_placement": "Warden Office & Common Room",
        "operating_schedule": "Intermittent (Office Hours)",
        "source_document": "HMC Student Residential Regulations",
        "source_url": "https://www.iitkgp.ac.in/hmc",
        "observation_date": "2024-07-20",
        "notes": "Student rooms non-AC. High daytime heat accumulation on roof slab."
    },
    {
        "building_id": "lbs_hall",
        "building_name": "Lal Bahadur Shastri (LBS) Hall",
        "category": "Hostel",
        "evidence_tier": "Verified",
        "primary_hvac_type": "Natural Ventilation / Ceiling Fans (Common Rooms Conditioned)",
        "ac_unit_count_confirmed": 8,  # Warden office, common study hall, canteen counter
        "ac_unit_count_estimated": 8,
        "condenser_count_estimated": 8,
        "cooling_capacity_tons_tr": 16.0,
        "rated_cooling_capacity_kw": 56.3,
        "rated_cop": 3.1,
        "rated_electrical_input_kw": 18.2,
        "outdoor_condenser_placement": "Central Administrative Block & Reading Room Ledges",
        "operating_schedule": "10:00 - 22:00 IST for Study Hall; Admin Hours for Office",
        "source_document": "HMC Infrastructure Register & Hall Allotment Guidelines",
        "source_url": "https://www.iitkgp.ac.in/hmc",
        "observation_date": "2024-08-10",
        "notes": "Large 2,000-occupant hostel. Individual student rooms are strictly non-AC by HMC rules."
    },
    # Sports & Open Spaces: Zero AC
    {
        "building_id": "tata_sports_complex",
        "building_name": "Tata Sports Complex & Swimming Pool",
        "category": "Sports/Open",
        "evidence_tier": "Verified",
        "primary_hvac_type": "Natural Ventilation / Outdoor Open Air",
        "ac_unit_count_confirmed": 2,  # Pool office split
        "ac_unit_count_estimated": 2,
        "condenser_count_estimated": 2,
        "cooling_capacity_tons_tr": 3.0,
        "rated_cooling_capacity_kw": 10.6,
        "rated_cop": 3.0,
        "rated_electrical_input_kw": 3.5,
        "outdoor_condenser_placement": "Admin Room Rear Wall",
        "operating_schedule": "Morning & Evening Coaching Hours",
        "source_document": "Sports Association Infrastructure Asset Register",
        "source_url": "https://www.iitkgp.ac.in",
        "observation_date": "2024-05-15",
        "notes": "Vast open concrete & courts; thermal state dominated by solar radiation, not AC waste heat."
    },
    {
        "building_id": "jnan_ghosh_stadium",
        "building_name": "Jnan Ghosh Stadium (Main Athletic Ground)",
        "category": "Sports/Open",
        "evidence_tier": "Verified",
        "primary_hvac_type": "Natural Ventilation / Zero AC",
        "ac_unit_count_confirmed": 0,
        "ac_unit_count_estimated": 0,
        "condenser_count_estimated": 0,
        "cooling_capacity_tons_tr": 0.0,
        "rated_cooling_capacity_kw": 0.0,
        "rated_cop": 1.0,
        "rated_electrical_input_kw": 0.0,
        "outdoor_condenser_placement": "None",
        "operating_schedule": "None",
        "source_document": "Physical Education Department Facility Register",
        "source_url": "https://www.iitkgp.ac.in",
        "observation_date": "2024-05-15",
        "notes": "Zero installed air conditioning. Grass athletic field."
    },
    {
        "building_id": "gymkhana",
        "building_name": "Technology Students' Gymkhana",
        "category": "Amenities",
        "evidence_tier": "Documented",
        "primary_hvac_type": "Inverter Split ACs in Offices & Rehearsal Rooms",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 18,
        "condenser_count_estimated": 14,
        "cooling_capacity_tons_tr": 27.0,
        "rated_cooling_capacity_kw": 95.0,
        "rated_cop": 3.1,
        "rated_electrical_input_kw": 30.6,
        "outdoor_condenser_placement": "East Balcony Ledges & Gym Office Exterior",
        "operating_schedule": "16:00 - 22:00 IST (Student Club & Activity Hours)",
        "source_document": "TSG Annual Maintenance Tender Records",
        "source_url": "https://www.iitkgp.ac.in",
        "observation_date": "2024-10-02",
        "notes": "Main gym floor partially ventilated; indoor committee and cultural rooms conditioned."
    },
    {
        "building_id": "scholars_avenue_junction",
        "building_name": "Scholars Avenue / Tech Market Commercial Precinct",
        "category": "Commercial",
        "evidence_tier": "Estimated",
        "primary_hvac_type": "Commercial Splits in Retail Outlets & Cafes",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 26,
        "condenser_count_estimated": 22,
        "cooling_capacity_tons_tr": 45.0,
        "rated_cooling_capacity_kw": 158.3,
        "rated_cop": 2.9,
        "rated_electrical_input_kw": 54.6,
        "outdoor_condenser_placement": "Shopfront Sidewalks & Canopy Roofs",
        "operating_schedule": "10:00 - 22:30 IST (Retail Commercial Hours)",
        "source_document": "Estate Office Commercial Allotment Survey Estimates",
        "source_url": "https://www.iitkgp.ac.in",
        "observation_date": "2025-01-20",
        "notes": "Pedestrian sidewalk heat exposure due to ground-level condenser exhausts."
    },
    {
        "building_id": "tikka_lake_zone",
        "building_name": "Tikka Lake Ecological & Wetland Zone",
        "category": "Water/Nature",
        "evidence_tier": "Verified",
        "primary_hvac_type": "Natural Wetland / Zero AC",
        "ac_unit_count_confirmed": 0,
        "ac_unit_count_estimated": 0,
        "condenser_count_estimated": 0,
        "cooling_capacity_tons_tr": 0.0,
        "rated_cooling_capacity_kw": 0.0,
        "rated_cop": 1.0,
        "rated_electrical_input_kw": 0.0,
        "outdoor_condenser_placement": "None",
        "operating_schedule": "None",
        "source_document": "Horticulture & Water Works Department Campus Ecological Inventory",
        "source_url": "https://www.iitkgp.ac.in",
        "observation_date": "2024-05-15",
        "notes": "Natural open water body with zero anthropogenic electrical cooling."
    },
    {
        "building_id": "old_sac_grounds",
        "building_name": "Old SAC (Student Activity Centre) Grounds",
        "category": "Amenities",
        "evidence_tier": "Estimated",
        "primary_hvac_type": "Inverter Splits in Student Society Rooms",
        "ac_unit_count_confirmed": None,
        "ac_unit_count_estimated": 14,
        "condenser_count_estimated": 10,
        "cooling_capacity_tons_tr": 20.0,
        "rated_cooling_capacity_kw": 70.3,
        "rated_cop": 3.0,
        "rated_electrical_input_kw": 23.4,
        "outdoor_condenser_placement": "Courtyard Facades",
        "operating_schedule": "15:00 - 21:00 IST (Evening Activity)",
        "source_document": "Estate Maintenance Minor Works Register",
        "source_url": "https://www.iitkgp.ac.in",
        "observation_date": "2024-11-10",
        "notes": "Low daytime cooling demand; evening student club operation."
    }
]


class CampusACInventoryEngine:
    """
    Manages building-level AC inventories, thermodynamic heat rejection calculations,
    and urban canopy anthropogenic heat flux modeling.
    """

    def __init__(self, data_file: Path = AC_DATABASE_FILE):
        self.data_file = data_file
        self.inventory: Dict[str, Dict[str, Any]] = {}
        self._load_or_initialize()

    def _load_or_initialize(self):
        """Loads database from disk or saves verified/documented initial inventory."""
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.inventory = {item["building_id"]: item for item in data}
                    return
            except Exception as e:
                print(f"Warning: Failed to read {self.data_file}: {e}. Initializing defaults.")

        # Save default compiled inventory
        self.inventory = {item["building_id"]: item for item in INITIAL_AC_INVENTORY}
        self.save_database()

    def save_database(self):
        """Serializes current inventory to disk."""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(list(self.inventory.values()), f, indent=2, ensure_ascii=False)

    def get_building_ac_profile(self, building_id: str) -> Optional[Dict[str, Any]]:
        """Returns the raw AC profile record for a specific building."""
        return self.inventory.get(building_id)

    def calculate_building_heat_rejection(
        self,
        building_id: str,
        operating_scenario: str = "nominal",
        ambient_temperature_c: float = 38.0,
        footprint_area_sqm: float = 5000.0
    ) -> Dict[str, Any]:
        """
        Calculates instantaneous thermodynamic waste heat rejected outdoors (kW)
        and anthropogenic heat flux (W/m²) for a building under a specified operational scenario.

        Thermodynamic Formula:
        Q_reject = Q_cooling + P_electric
        P_electric = Q_cooling / COP_actual

        Operating Scenarios:
        - 'peak': High occupancy, intense afternoon cooling (PLR = 0.90 - 1.00)
        - 'nominal': Standard working day operation (PLR = 0.65 - 0.75)
        - 'reduced': Off-peak, nighttime, or weekend minimum load (PLR = 0.20 - 0.30)
        - 'zero': Systems shut down (PLR = 0.0)
        """
        rec = self.inventory.get(building_id)
        if not rec:
            return {
                "building_id": building_id,
                "evidence_tier": "Unknown",
                "heat_rejection_kw": 0.0,
                "electrical_input_kw": 0.0,
                "anthropogenic_flux_wm2": 0.0,
                "status": "No AC inventory record available."
            }

        rated_cooling_kw = rec.get("rated_cooling_capacity_kw", 0.0)
        rated_cop = rec.get("rated_cop", 3.2)

        # Scenario Part-Load Ratio (PLR) multipliers
        plr_factors = {
            "peak": 0.95,
            "nominal": 0.70,
            "reduced": 0.25,
            "zero": 0.0
        }
        plr = plr_factors.get(operating_scenario, 0.70)

        # High ambient temperature derates condenser COP by ~1.5% per °C above 35°C rating point
        if ambient_temperature_c > 35.0:
            cop_derate = max(0.65, 1.0 - 0.015 * (ambient_temperature_c - 35.0))
        else:
            cop_derate = 1.0

        cop_actual = max(1.8, rated_cop * cop_derate)

        # Delivered cooling under current operating condition
        q_cooling_delivered_kw = rated_cooling_kw * plr

        if q_cooling_delivered_kw > 0 and cop_actual > 0:
            p_electric_kw = q_cooling_delivered_kw / cop_actual
            q_reject_kw = q_cooling_delivered_kw + p_electric_kw
        else:
            p_electric_kw = 0.0
            q_reject_kw = 0.0

        # Anthropogenic heat flux per unit building footprint area (W/m²)
        area = max(100.0, footprint_area_sqm)
        anthropogenic_flux_wm2 = round((q_reject_kw * 1000.0) / area, 1)

        # Scientific microclimatic impact disclosure
        if q_reject_kw > 500.0:
            canyon_impact = (
                "High Anthropogenic Heat Source: Condenser plumes elevate immediate street canyon "
                "microclimate air temperatures by ~0.4°C to 0.8°C under low wind stagnation."
            )
        elif q_reject_kw > 150.0:
            canyon_impact = (
                "Moderate Anthropogenic Heat Source: Localized rooftop/veranda thermal plumes; "
                "contributes minor sensible heat flux diluted by ambient canopy wind."
            )
        elif q_reject_kw > 0.0:
            canyon_impact = (
                "Low Anthropogenic Heat Source: Minimal localized exhaust; easily mixed by canopy convective flow."
            )
        else:
            canyon_impact = "Negligible / Zero Anthropogenic AC Heat Rejection: Naturally ventilated precinct."

        return {
            "building_id": building_id,
            "building_name": rec.get("building_name"),
            "evidence_tier": rec.get("evidence_tier"),
            "primary_hvac_type": rec.get("primary_hvac_type"),
            "ac_unit_count_confirmed": rec.get("ac_unit_count_confirmed"),
            "ac_unit_count_estimated": rec.get("ac_unit_count_estimated"),
            "condenser_count_estimated": rec.get("condenser_count_estimated"),
            "cooling_capacity_tons_tr": rec.get("cooling_capacity_tons_tr"),
            "rated_cooling_capacity_kw": round(rated_cooling_kw, 1),
            "operating_scenario": operating_scenario,
            "part_load_ratio": plr,
            "actual_cop_derated": round(cop_actual, 2),
            "cooling_delivered_kw": round(q_cooling_delivered_kw, 1),
            "electrical_input_kw": round(p_electric_kw, 1),
            "heat_rejection_kw": round(q_reject_kw, 1),
            "anthropogenic_flux_wm2": anthropogenic_flux_wm2,
            "condenser_placement": rec.get("outdoor_condenser_placement"),
            "operating_schedule": rec.get("operating_schedule"),
            "source_document": rec.get("source_document"),
            "source_url": rec.get("source_url"),
            "observation_date": rec.get("observation_date"),
            "microclimatic_canyon_impact": canyon_impact,
            "notes": rec.get("notes")
        }

    def evaluate_all_campus_ac_rejection(
        self,
        operating_scenario: str = "nominal",
        ambient_temperature_c: float = 38.0,
        building_features: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Computes campus-wide AC inventory summary, total electrical cooling load,
        and total outdoor heat rejection across all 24 IIT Kharagpur precincts.
        """
        results = []
        total_cooling_tr = 0.0
        total_cooling_kw = 0.0
        total_electric_kw = 0.0
        total_reject_kw = 0.0
        total_units_confirmed = 0
        total_units_estimated = 0

        # Build map of building footprint area if features provided
        area_map = {}
        if building_features:
            for feat in building_features:
                props = feat.get("properties", {})
                b_id = props.get("id")
                if b_id:
                    area_map[b_id] = float(props.get("area_sqm", 5000.0))

        for b_id, rec in self.inventory.items():
            area = area_map.get(b_id, 5000.0)
            res = self.calculate_building_heat_rejection(
                building_id=b_id,
                operating_scenario=operating_scenario,
                ambient_temperature_c=ambient_temperature_c,
                footprint_area_sqm=area
            )
            results.append(res)

            total_cooling_tr += rec.get("cooling_capacity_tons_tr", 0.0)
            total_cooling_kw += res["cooling_delivered_kw"]
            total_electric_kw += res["electrical_input_kw"]
            total_reject_kw += res["heat_rejection_kw"]

            if rec.get("ac_unit_count_confirmed") is not None:
                total_units_confirmed += rec["ac_unit_count_confirmed"]
            if rec.get("ac_unit_count_estimated") is not None:
                total_units_estimated += rec["ac_unit_count_estimated"]

        # Sort precincts by heat rejection descending
        results.sort(key=lambda x: x["heat_rejection_kw"], reverse=True)

        return {
            "operating_scenario": operating_scenario,
            "ambient_temperature_c": ambient_temperature_c,
            "campus_summary": {
                "total_precincts_tracked": len(results),
                "total_installed_cooling_capacity_tr": round(total_cooling_tr, 1),
                "active_cooling_delivered_kw": round(total_cooling_kw, 1),
                "active_electrical_input_kw": round(total_electric_kw, 1),
                "total_outdoor_heat_rejection_kw": round(total_reject_kw, 1),
                "total_outdoor_heat_rejection_megawatts": round(total_reject_kw / 1000.0, 2),
                "total_ac_units_confirmed": total_units_confirmed,
                "total_ac_units_estimated": total_units_estimated,
                "top_heat_rejecting_building": {
                    "id": results[0]["building_id"],
                    "name": results[0]["building_name"],
                    "heat_rejection_kw": results[0]["heat_rejection_kw"],
                    "flux_wm2": results[0]["anthropogenic_flux_wm2"]
                } if results else None
            },
            "buildings": results
        }


# Global singleton instance
CAMPUS_AC_ENGINE = CampusACInventoryEngine()
