"""
StockPulse Mock Data Generator
Generates consistent, hand-authored seed data for the prototype.
Real facility coordinates from Madurai district, Tamil Nadu.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path


# Real PHC locations in Madurai district (approximate coordinates)
FACILITIES = [
    {
        "facility_id": "PHC_01",
        "name": "PHC Madurai North",
        "latitude": 9.9252,
        "longitude": 78.1198,
        "district": "Madurai",
        "type": "PHC"
    },
    {
        "facility_id": "PHC_02",
        "name": "PHC Madurai South",
        "latitude": 9.8800,
        "longitude": 78.1200,
        "district": "Madurai",
        "type": "PHC"
    },
    {
        "facility_id": "PHC_03",
        "name": "PHC Thirumangalam",
        "latitude": 9.7900,
        "longitude": 77.9800,
        "district": "Madurai",
        "type": "PHC"
    },
    {
        "facility_id": "PHC_04",
        "name": "PHC Melur",
        "latitude": 10.0300,
        "longitude": 78.3300,
        "district": "Madurai",
        "type": "PHC"
    },
    {
        "facility_id": "PHC_05",
        "name": "CHC Usilampatti",
        "latitude": 9.9700,
        "longitude": 77.7800,
        "district": "Madurai",
        "type": "CHC"
    },
]

# 3 items: 1 fast-moving medicine (ORS), 1 vaccine (Measles), 1 slow-moving control
ITEMS = [
    {
        "item_id": "ORS",
        "item_name": "Oral Rehydration Salts",
        "category": "medicine",
        "unit": "packets"
    },
    {
        "item_id": "MEASLES_VAX",
        "item_name": "Measles Vaccine",
        "category": "vaccine",
        "unit": "doses"
    },
    {
        "item_id": "PARACETAMOL",
        "item_name": "Paracetamol 500mg",
        "category": "medicine",
        "unit": "tablets"
    },
]

# Stock levels per facility per item (carefully crafted for demo)
# PHC_01: ORS trending to stockout, MEASLES_VAX normal, PARACETAMOL normal
# PHC_04: ORS surplus (donor), MEASLES_VAX normal, PARACETAMOL normal
STOCK_ITEMS = [
    # PHC_01 - The facility heading toward stockout
    {"item_id": "ORS", "facility_id": "PHC_01", "current_stock": 40, "supplier_lead_time_days": 3, "last_updated": "2026-09-24T08:00:00"},
    {"item_id": "MEASLES_VAX", "facility_id": "PHC_01", "current_stock": 120, "supplier_lead_time_days": 7, "last_updated": "2026-09-24T08:00:00"},
    {"item_id": "PARACETAMOL", "facility_id": "PHC_01", "current_stock": 5000, "supplier_lead_time_days": 2, "last_updated": "2026-09-24T08:00:00"},
    
    # PHC_02 - Normal levels
    {"item_id": "ORS", "facility_id": "PHC_02", "current_stock": 180, "supplier_lead_time_days": 3, "last_updated": "2026-09-24T08:00:00"},
    {"item_id": "MEASLES_VAX", "facility_id": "PHC_02", "current_stock": 150, "supplier_lead_time_days": 7, "last_updated": "2026-09-24T08:00:00"},
    {"item_id": "PARACETAMOL", "facility_id": "PHC_02", "current_stock": 4500, "supplier_lead_time_days": 2, "last_updated": "2026-09-24T08:00:00"},
    
    # PHC_03 - Normal levels
    {"item_id": "ORS", "facility_id": "PHC_03", "current_stock": 200, "supplier_lead_time_days": 3, "last_updated": "2026-09-24T08:00:00"},
    {"item_id": "MEASLES_VAX", "facility_id": "PHC_03", "current_stock": 100, "supplier_lead_time_days": 7, "last_updated": "2026-09-24T08:00:00"},
    {"item_id": "PARACETAMOL", "facility_id": "PHC_03", "current_stock": 6000, "supplier_lead_time_days": 2, "last_updated": "2026-09-24T08:00:00"},
    
    # PHC_04 - SURPLUS donor for ORS
    {"item_id": "ORS", "facility_id": "PHC_04", "current_stock": 500, "supplier_lead_time_days": 3, "last_updated": "2026-09-24T08:00:00"},
    {"item_id": "MEASLES_VAX", "facility_id": "PHC_04", "current_stock": 80, "supplier_lead_time_days": 7, "last_updated": "2026-09-24T08:00:00"},
    {"item_id": "PARACETAMOL", "facility_id": "PHC_04", "current_stock": 3000, "supplier_lead_time_days": 2, "last_updated": "2026-09-24T08:00:00"},
    
    # PHC_05 - CHC, normal levels
    {"item_id": "ORS", "facility_id": "PHC_05", "current_stock": 300, "supplier_lead_time_days": 3, "last_updated": "2026-09-24T08:00:00"},
    {"item_id": "MEASLES_VAX", "facility_id": "PHC_05", "current_stock": 200, "supplier_lead_time_days": 7, "last_updated": "2026-09-24T08:00:00"},
    {"item_id": "PARACETAMOL", "facility_id": "PHC_05", "current_stock": 8000, "supplier_lead_time_days": 2, "last_updated": "2026-09-24T08:00:00"},
]

# Consumption log: 14 days per item per facility
# PHC_01 ORS: trending up consumption (20->35) to create stockout pressure
# PHC_04 ORS: steady low consumption (surplus facility)
# Others: steady consumption

def generate_consumption_log():
    log = []
    log_id = 1
    base_date = datetime(2026, 9, 10)  # 14 days before 2026-09-24
    
    # Consumption patterns per facility per item (last 14 days)
    # Key: (facility_id, item_id) -> list of 14 daily quantities
    patterns = {
        # PHC_01 - ORS trending UP (creating stockout risk)
        ("PHC_01", "ORS"): [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 33, 35],
        ("PHC_01", "MEASLES_VAX"): [8, 8, 7, 8, 9, 8, 7, 8, 8, 7, 8, 8, 7, 8],
        ("PHC_01", "PARACETAMOL"): [45, 48, 42, 50, 47, 44, 46, 49, 43, 45, 47, 44, 46, 48],
        
        # PHC_02 - Steady
        ("PHC_02", "ORS"): [12, 11, 13, 12, 11, 12, 13, 12, 11, 12, 12, 11, 12, 13],
        ("PHC_02", "MEASLES_VAX"): [6, 7, 6, 6, 7, 6, 6, 7, 6, 6, 7, 6, 6, 7],
        ("PHC_02", "PARACETAMOL"): [40, 42, 38, 41, 39, 40, 42, 39, 41, 40, 38, 41, 40, 39],
        
        # PHC_03 - Steady
        ("PHC_03", "ORS"): [10, 11, 10, 11, 10, 10, 11, 10, 11, 10, 10, 11, 10, 10],
        ("PHC_03", "MEASLES_VAX"): [5, 5, 6, 5, 5, 6, 5, 5, 6, 5, 5, 6, 5, 5],
        ("PHC_03", "PARACETAMOL"): [50, 48, 52, 49, 51, 47, 50, 48, 52, 49, 50, 48, 51, 49],
        
        # PHC_04 - SURPLUS donor (low ORS consumption)
        ("PHC_04", "ORS"): [5, 6, 5, 5, 6, 5, 5, 6, 5, 5, 6, 5, 5, 5],
        ("PHC_04", "MEASLES_VAX"): [4, 4, 5, 4, 4, 5, 4, 4, 5, 4, 4, 5, 4, 4],
        ("PHC_04", "PARACETAMOL"): [30, 28, 32, 29, 31, 27, 30, 28, 32, 29, 30, 28, 31, 29],
        
        # PHC_05 - CHC, steady
        ("PHC_05", "ORS"): [15, 14, 16, 15, 14, 15, 16, 15, 14, 15, 15, 14, 15, 16],
        ("PHC_05", "MEASLES_VAX"): [10, 9, 11, 10, 9, 10, 11, 10, 9, 10, 10, 9, 10, 11],
        ("PHC_05", "PARACETAMOL"): [60, 58, 62, 59, 61, 57, 60, 58, 62, 59, 60, 58, 61, 59],
    }
    
    for (facility_id, item_id), quantities in patterns.items():
        for day_offset, qty in enumerate(quantities):
            log.append({
                "log_id": log_id,
                "item_id": item_id,
                "facility_id": facility_id,
                "date": (base_date + timedelta(days=day_offset)).strftime("%Y-%m-%d"),
                "quantity_dispensed": qty
            })
            log_id += 1
    
    return log


# Disruption scenario: supplier delay for ORS at PHC_01
DISRUPTION_SCENARIOS = [
    {
        "scenario_id": "SUPPLIER_DELAY_3D_ORS",
        "item_id": "ORS",
        "facility_id": "PHC_01",
        "delay_days": 3
    }
]


def main():
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    # Generate consumption log
    consumption_log = generate_consumption_log()
    
    # Write all data files
    datasets = {
        "facilities": FACILITIES,
        "items": ITEMS,
        "stock_items": STOCK_ITEMS,
        "consumption_log": consumption_log,
        "disruption_scenarios": DISRUPTION_SCENARIOS,
    }
    
    for name, data in datasets.items():
        filepath = output_dir / f"{name}.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Generated {filepath} with {len(data)} records")
    
    print("\n[OK] Seed data generated successfully!")
    print(f"Data directory: {output_dir}")
    
    # Print summary for verification
    print("\n--- Quick Verification ---")
    phc01_ors_stock = next(s for s in STOCK_ITEMS if s["facility_id"] == "PHC_01" and s["item_id"] == "ORS")
    phc01_ors_consumption = [c for c in consumption_log if c["facility_id"] == "PHC_01" and c["item_id"] == "ORS"]
    avg_consumption = sum(c["quantity_dispensed"] for c in phc01_ors_consumption[-7:]) / 7
    days_remaining = phc01_ors_stock["current_stock"] / avg_consumption
    lead_time = phc01_ors_stock["supplier_lead_time_days"]
    print(f"PHC_01 ORS: stock={phc01_ors_stock['current_stock']}, 7-day avg consumption={avg_consumption:.1f}/day")
    print(f"  Days remaining: {days_remaining:.1f}, Lead time: {lead_time} days")
    print(f"  Risk level: {'critical' if days_remaining < lead_time else 'watch' if days_remaining < lead_time * 1.5 else 'normal'}")
    
    phc04_ors_stock = next(s for s in STOCK_ITEMS if s["facility_id"] == "PHC_04" and s["item_id"] == "ORS")
    phc04_ors_consumption = [c for c in consumption_log if c["facility_id"] == "PHC_04" and c["item_id"] == "ORS"]
    avg_consumption_04 = sum(c["quantity_dispensed"] for c in phc04_ors_consumption[-7:]) / 7
    days_remaining_04 = phc04_ors_stock["current_stock"] / avg_consumption_04
    print(f"\nPHC_04 ORS: stock={phc04_ors_stock['current_stock']}, 7-day avg consumption={avg_consumption_04:.1f}/day")
    print(f"  Days remaining: {days_remaining_04:.1f}, Lead time: {phc04_ors_stock['supplier_lead_time_days']} days")
    print(f"  Surplus buffer: {days_remaining_04 / phc04_ors_stock['supplier_lead_time_days']:.1f}x lead time")


if __name__ == "__main__":
    main()