"""
StockPulse Core Algorithms
Transparent, explainable calculations for runway forecasting,
surplus matching, and cascade risk checking.
"""

from dataclasses import dataclass
from typing import Optional
from math import radians, sin, cos, sqrt, atan2


# ============================================================
# Data loading (in-memory from JSON)
# ============================================================

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

_facilities = None
_items = None
_stock_items = None
_consumption_log = None
_disruption_scenarios = None


def load_data():
    global _facilities, _items, _stock_items, _consumption_log, _disruption_scenarios
    with open(DATA_DIR / "facilities.json") as f:
        _facilities = {f["facility_id"]: f for f in json.load(f)}
    with open(DATA_DIR / "items.json") as f:
        _items = {i["item_id"]: i for i in json.load(f)}
    with open(DATA_DIR / "stock_items.json") as f:
        _stock_items = {(s["item_id"], s["facility_id"]): s for s in json.load(f)}
    with open(DATA_DIR / "consumption_log.json") as f:
        _consumption_log = json.load(f)
    with open(DATA_DIR / "disruption_scenarios.json") as f:
        _disruption_scenarios = json.load(f)


def get_facility(facility_id: str) -> Optional[dict]:
    if _facilities is None:
        load_data()
    return _facilities.get(facility_id)


def get_item(item_id: str) -> Optional[dict]:
    if _items is None:
        load_data()
    return _items.get(item_id)


def get_stock(item_id: str, facility_id: str) -> Optional[dict]:
    if _stock_items is None:
        load_data()
    return _stock_items.get((item_id, facility_id))


def get_consumption_log(item_id: str, facility_id: str, days: int = 14) -> list:
    if _consumption_log is None:
        load_data()
    return [
        c for c in _consumption_log
        if c["item_id"] == item_id and c["facility_id"] == facility_id
    ][-days:]


def get_disruption_scenario(scenario_id: str) -> Optional[dict]:
    if _disruption_scenarios is None:
        load_data()
    for s in _disruption_scenarios:
        if s["scenario_id"] == scenario_id:
            return s
    return None


# ============================================================
# Core Calculations
# ============================================================

def avg_daily_consumption(item_id: str, facility_id: str, window_days: int = 7) -> float:
    """Simple moving average of last `window_days` entries."""
    log = get_consumption_log(item_id, facility_id, window_days)
    if not log:
        return 0.0
    return sum(c["quantity_dispensed"] for c in log) / len(log)


def days_remaining(current_stock: int, daily_consumption: float) -> float:
    """How many days until stock runs out at current consumption rate."""
    if daily_consumption <= 0:
        return float("inf")
    return current_stock / daily_consumption


def lead_time_days(item_id: str, facility_id: str) -> int:
    stock = get_stock(item_id, facility_id)
    return stock["supplier_lead_time_days"] if stock else 3


def risk_level(days_rem: float, lead_time: int) -> str:
    """Classify risk based on days remaining vs supplier lead time."""
    if days_rem < lead_time:
        return "critical"
    elif days_rem < lead_time * 1.5:
        return "watch"
    else:
        return "normal"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance between two lat/lon points in kilometers."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


# ============================================================
# Forecast Engine
# ============================================================

@dataclass
class ForecastResult:
    item_id: str
    facility_id: str
    current_stock: int
    daily_consumption: float
    days_remaining: float
    lead_time_days: int
    risk_level: str
    item_name: str
    unit: str

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "facility_id": self.facility_id,
            "item_name": self.item_name,
            "unit": self.unit,
            "current_stock": self.current_stock,
            "daily_consumption": round(self.daily_consumption, 1),
            "days_remaining": round(self.days_remaining, 1),
            "lead_time_days": self.lead_time_days,
            "risk_level": self.risk_level,
        }


def forecast_item_at_facility(item_id: str, facility_id: str) -> Optional[ForecastResult]:
    """Complete forecast for one item at one facility."""
    stock = get_stock(item_id, facility_id)
    item = get_item(item_id)
    facility = get_facility(facility_id)
    if not stock or not item or not facility:
        return None
    
    daily_cons = avg_daily_consumption(item_id, facility_id)
    days_rem = days_remaining(stock["current_stock"], daily_cons)
    lt = lead_time_days(item_id, facility_id)
    risk = risk_level(days_rem, lt)
    
    return ForecastResult(
        item_id=item_id,
        facility_id=facility_id,
        current_stock=stock["current_stock"],
        daily_consumption=daily_cons,
        days_remaining=days_rem,
        lead_time_days=lt,
        risk_level=risk,
        item_name=item["item_name"],
        unit=item["unit"],
    )


def forecast_facility(facility_id: str) -> list[ForecastResult]:
    """Forecast all items at a facility."""
    if _stock_items is None:
        load_data()
    results = []
    for (item_id, fid), stock in _stock_items.items():
        if fid == facility_id:
            result = forecast_item_at_facility(item_id, facility_id)
            if result:
                results.append(result)
    return results


def forecast_all() -> list[ForecastResult]:
    """Forecast all item/facility combinations."""
    if _stock_items is None:
        load_data()
    results = []
    for (item_id, facility_id) in _stock_items.keys():
        result = forecast_item_at_facility(item_id, facility_id)
        if result:
            results.append(result)
    return results


# ============================================================
# Surplus Matcher
# ============================================================

@dataclass
class SurplusCandidate:
    facility_id: str
    facility_name: str
    distance_km: float
    current_stock: int
    daily_consumption: float
    days_remaining: float
    lead_time_days: int
    transferable_qty: int

    def to_dict(self):
        return {
            "facility_id": self.facility_id,
            "facility_name": self.facility_name,
            "distance_km": round(self.distance_km, 1),
            "current_stock": self.current_stock,
            "daily_consumption": round(self.daily_consumption, 1),
            "days_remaining": round(self.days_remaining, 1),
            "lead_time_days": self.lead_time_days,
            "transferable_qty": self.transferable_qty,
        }


def find_surplus_facilities(
    item_id: str,
    requesting_facility_id: str,
    radius_km: float = 30.0
) -> list[SurplusCandidate]:
    """Find nearby facilities with genuine surplus for the item."""
    if _facilities is None:
        load_data()
    
    requesting_facility = get_facility(requesting_facility_id)
    if not requesting_facility:
        return []
    
    req_lat = requesting_facility["latitude"]
    req_lon = requesting_facility["longitude"]
    req_lead_time = lead_time_days(item_id, requesting_facility_id)
    
    candidates = []
    for facility in _facilities.values():
        if facility["facility_id"] == requesting_facility_id:
            continue
        
        # Check distance
        dist = haversine_km(req_lat, req_lon, facility["latitude"], facility["longitude"])
        if dist > radius_km:
            continue
        
        # Check if they have this item
        stock = get_stock(item_id, facility["facility_id"])
        if not stock:
            continue
        
        # Calculate their runway
        their_consumption = avg_daily_consumption(item_id, facility["facility_id"])
        their_days = days_remaining(stock["current_stock"], their_consumption)
        their_lead_time = lead_time_days(item_id, facility["facility_id"])
        
        # Only a genuine surplus if they have 2x lead time buffer
        if their_days > their_lead_time * 2:
            # Transferable = stock - (consumption * lead_time * 1.5 safety margin)
            safety_stock = their_consumption * their_lead_time * 1.5
            transferable = int(stock["current_stock"] - safety_stock)
            if transferable > 0:
                candidates.append(SurplusCandidate(
                    facility_id=facility["facility_id"],
                    facility_name=facility["name"],
                    distance_km=dist,
                    current_stock=stock["current_stock"],
                    daily_consumption=their_consumption,
                    days_remaining=their_days,
                    lead_time_days=their_lead_time,
                    transferable_qty=transferable,
                ))
    
    # Sort by most transferable first
    return sorted(candidates, key=lambda x: -x.transferable_qty)


# ============================================================
# Cascade Checker
# ============================================================

def check_cascade_risk(
    donor_facility_id: str,
    item_id: str,
    transfer_qty: int
) -> tuple[bool, float]:
    """
    Check if donor facility remains safe after transfer.
    Returns (is_safe, new_days_remaining).
    """
    stock = get_stock(item_id, donor_facility_id)
    if not stock:
        return False, 0.0
    
    consumption = avg_daily_consumption(item_id, donor_facility_id)
    remaining_stock = stock["current_stock"] - transfer_qty
    new_days = days_remaining(remaining_stock, consumption)
    lead_time = lead_time_days(item_id, donor_facility_id)
    
    # Safe if donor still has at least lead_time days after transfer
    is_safe = new_days >= lead_time
    return is_safe, new_days


# ============================================================
# Transfer Recommendation (combines surplus + cascade)
# ============================================================

@dataclass
class TransferRecommendation:
    item_id: str
    item_name: str
    requesting_facility_id: str
    requesting_facility_name: str
    source_facility_id: str
    source_facility_name: str
    quantity: int
    distance_km: float
    requester_days_before: float
    requester_days_after: float
    donor_days_before: float
    donor_days_after: float
    donor_safe: bool

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "item_name": self.item_name,
            "requesting_facility_id": self.requesting_facility_id,
            "requesting_facility_name": self.requesting_facility_name,
            "source_facility_id": self.source_facility_id,
            "source_facility_name": self.source_facility_name,
            "quantity": self.quantity,
            "distance_km": round(self.distance_km, 1),
            "requester_days_before": round(self.requester_days_before, 1),
            "requester_days_after": round(self.requester_days_after, 1),
            "donor_days_before": round(self.donor_days_before, 1),
            "donor_days_after": round(self.donor_days_after, 1),
            "donor_safe": self.donor_safe,
        }


def recommend_transfer(
    item_id: str,
    requesting_facility_id: str,
    needed_qty: Optional[int] = None
) -> Optional[TransferRecommendation]:
    """
    Full recommendation: find best surplus donor, verify cascade safety,
    calculate post-transfer runways for both facilities.
    """
    requesting_facility = get_facility(requesting_facility_id)
    item = get_item(item_id)
    if not requesting_facility or not item:
        return None
    
    # How much does requester need? Default: enough to reach 2x lead time
    req_stock = get_stock(item_id, requesting_facility_id)
    req_consumption = avg_daily_consumption(item_id, requesting_facility_id)
    req_lead_time = lead_time_days(item_id, requesting_facility_id)
    req_days_before = days_remaining(req_stock["current_stock"], req_consumption)
    
    if needed_qty is None:
        # Target: 2x lead time days of stock
        target_stock = req_consumption * req_lead_time * 2
        needed_qty = int(target_stock - req_stock["current_stock"])
    
    if needed_qty <= 0:
        return None
    
    # Find surplus candidates
    surpluses = find_surplus_facilities(item_id, requesting_facility_id)
    if not surpluses:
        return None
    
    # Try each candidate until we find one that passes cascade check
    for candidate in surpluses:
        transfer_qty = min(needed_qty, candidate.transferable_qty)
        
        # Cascade check
        donor_safe, donor_days_after = check_cascade_risk(
            candidate.facility_id, item_id, transfer_qty
        )
        
        if donor_safe:
            # Calculate requester's new runway
            req_new_stock = req_stock["current_stock"] + transfer_qty
            req_days_after = days_remaining(req_new_stock, req_consumption)
            
            return TransferRecommendation(
                item_id=item_id,
                item_name=item["item_name"],
                requesting_facility_id=requesting_facility_id,
                requesting_facility_name=requesting_facility["name"],
                source_facility_id=candidate.facility_id,
                source_facility_name=candidate.facility_name,
                quantity=transfer_qty,
                distance_km=candidate.distance_km,
                requester_days_before=req_days_before,
                requester_days_after=req_days_after,
                donor_days_before=candidate.days_remaining,
                donor_days_after=donor_days_after,
                donor_safe=True,
            )
    
    # No safe donor found
    return None


# ============================================================
# Disruption Simulation
# ============================================================

@dataclass
class SimulationResult:
    item_id: str
    facility_id: str
    scenario_id: str
    delay_days: int
    original_risk: str
    simulated_risk: str
    original_days_remaining: float
    simulated_days_remaining: float  # Same stock/consumption, but risk reassessed with longer lead time
    original_lead_time: int
    simulated_lead_time: int

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "facility_id": self.facility_id,
            "scenario_id": self.scenario_id,
            "delay_days": self.delay_days,
            "original_risk": self.original_risk,
            "simulated_risk": self.simulated_risk,
            "original_days_remaining": round(self.original_days_remaining, 1),
            "simulated_days_remaining": round(self.simulated_days_remaining, 1),
            "original_lead_time": self.original_lead_time,
            "simulated_lead_time": self.simulated_lead_time,
        }


def simulate_disruption(
    item_id: str,
    facility_id: str,
    delay_days: int
) -> Optional[SimulationResult]:
    """
    Simulate a supply disruption by adding delay_days to lead time.
    Recomputes risk level with the extended lead time.
    """
    forecast = forecast_item_at_facility(item_id, facility_id)
    if not forecast:
        return None
    
    original_lead_time = forecast.lead_time_days
    simulated_lead_time = original_lead_time + delay_days
    simulated_risk = risk_level(forecast.days_remaining, simulated_lead_time)
    
    return SimulationResult(
        item_id=item_id,
        facility_id=facility_id,
        scenario_id=f"SUPPLIER_DELAY_{delay_days}D",
        delay_days=delay_days,
        original_risk=forecast.risk_level,
        simulated_risk=simulated_risk,
        original_days_remaining=forecast.days_remaining,
        simulated_days_remaining=forecast.days_remaining,  # Stock doesn't change, just risk assessment
        original_lead_time=original_lead_time,
        simulated_lead_time=simulated_lead_time,
    )


def simulate_scenario(scenario_id: str) -> Optional[SimulationResult]:
    """Run a pre-defined disruption scenario."""
    scenario = get_disruption_scenario(scenario_id)
    if not scenario:
        return None
    return simulate_disruption(
        scenario["item_id"],
        scenario["facility_id"],
        scenario["delay_days"]
    )


# ============================================================
# Apply Transfer (updates in-memory stock for demo)
# ============================================================

def apply_transfer(transfer: TransferRecommendation) -> bool:
    """
    Apply a transfer by updating in-memory stock.
    Returns True if successful.
    """
    if _stock_items is None:
        load_data()
    
    # Deduct from donor
    donor_key = (transfer.item_id, transfer.source_facility_id)
    recipient_key = (transfer.item_id, transfer.requesting_facility_id)
    
    if donor_key not in _stock_items or recipient_key not in _stock_items:
        return False
    
    donor_stock = _stock_items[donor_key]
    recipient_stock = _stock_items[recipient_key]
    
    if donor_stock["current_stock"] < transfer.quantity:
        return False
    
    donor_stock["current_stock"] -= transfer.quantity
    recipient_stock["current_stock"] += transfer.quantity
    
    return True


# ============================================================
# Test / Demo
# ============================================================

if __name__ == "__main__":
    load_data()
    
    print("=== StockPulse Core Algorithms Test ===\n")
    
    # Test 1: Forecast for PHC_01
    print("1. Forecast for PHC_01:")
    for f in forecast_facility("PHC_01"):
        d = f.to_dict()
        print(f"  {d['item_name']}: stock={d['current_stock']}, "
              f"avg_day={d['daily_consumption']}, days={d['days_remaining']}, "
              f"lead_time={d['lead_time_days']}, risk={d['risk_level']}")
    
    # Test 2: Surplus for ORS at PHC_01
    print("\n2. Surplus candidates for ORS near PHC_01:")
    surpluses = find_surplus_facilities("ORS", "PHC_01")
    for s in surpluses:
        d = s.to_dict()
        print(f"  {d['facility_name']} ({d['facility_id']}): "
              f"dist={d['distance_km']}km, stock={d['current_stock']}, "
              f"transferable={d['transferable_qty']}, days={d['days_remaining']}")
    
    # Test 3: Transfer recommendation
    print("\n3. Transfer recommendation for ORS at PHC_01:")
    rec = recommend_transfer("ORS", "PHC_01")
    if rec:
        d = rec.to_dict()
        print(f"  From: {d['source_facility_name']} ({d['source_facility_id']})")
        print(f"  Qty: {d['quantity']}, Distance: {d['distance_km']}km")
        print(f"  Requester: {d['requester_days_before']} -> {d['requester_days_after']} days")
        print(f"  Donor: {d['donor_days_before']} -> {d['donor_days_after']} days (safe: {d['donor_safe']})")
    else:
        print("  No recommendation available")
    
    # Test 4: Disruption simulation
    print("\n4. Disruption simulation (3-day supplier delay for ORS at PHC_01):")
    sim = simulate_disruption("ORS", "PHC_01", 3)
    if sim:
        d = sim.to_dict()
        print(f"  Original risk: {d['original_risk']} (lead time: {d['original_lead_time']} days)")
        print(f"  Simulated risk: {d['simulated_risk']} (lead time: {d['simulated_lead_time']} days)")
        print(f"  Days remaining unchanged: {d['original_days_remaining']} days")