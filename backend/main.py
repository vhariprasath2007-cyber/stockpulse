"""
StockPulse FastAPI Backend
All 8 endpoints as specified.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

from core import (
    load_data,
    forecast_facility,
    forecast_all,
    forecast_item_at_facility,
    find_surplus_facilities,
    recommend_transfer,
    simulate_disruption,
    simulate_scenario,
    apply_transfer,
    get_facility,
    get_item,
    get_stock,
    TransferRecommendation,
)

# Load data on startup
load_data()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="StockPulse API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Request/Response Models
# ============================================================

class TransferApplyRequest(BaseModel):
    item_id: str
    source_facility_id: str
    destination_facility_id: str
    quantity: int


class SimulateRequest(BaseModel):
    item_id: str
    facility_id: str
    delay_days: int


class ExplainRequest(BaseModel):
    facility: str
    item: str
    days_remaining: float
    risk_level: str
    recommended_transfer: Optional[dict] = None
    post_transfer_days_remaining: Optional[float] = None


# ============================================================
# Endpoints
# ============================================================

@app.get("/facilities")
def list_facilities():
    """List all facilities with current risk summary."""
    forecasts = forecast_all()
    
    # Group by facility
    facility_summary = {}
    for f in forecasts:
        fid = f.facility_id
        if fid not in facility_summary:
            facility = get_facility(fid)
            facility_summary[fid] = {
                "facility_id": fid,
                "name": facility["name"] if facility else fid,
                "district": facility["district"] if facility else "",
                "type": facility["type"] if facility else "",
                "latitude": facility["latitude"] if facility else 0,
                "longitude": facility["longitude"] if facility else 0,
                "items": [],
                "overall_risk": "normal",
            }
        facility_summary[fid]["items"].append(f.to_dict())
    
    # Compute overall risk per facility (worst item risk)
    risk_order = {"critical": 3, "watch": 2, "normal": 1}
    for summary in facility_summary.values():
        worst = max(summary["items"], key=lambda x: risk_order.get(x["risk_level"], 0), default=None)
        summary["overall_risk"] = worst["risk_level"] if worst else "normal"
    
    return list(facility_summary.values())


@app.get("/facilities/{facility_id}/stock")
def facility_stock(facility_id: str):
    """Stock + runway for every item at a facility."""
    facility = get_facility(facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    
    forecasts = forecast_facility(facility_id)
    return {
        "facility_id": facility_id,
        "facility_name": facility["name"],
        "items": [f.to_dict() for f in forecasts],
    }


@app.get("/forecast/{item_id}/{facility_id}")
def forecast_endpoint(item_id: str, facility_id: str):
    """Runway + risk level for one item at one facility."""
    result = forecast_item_at_facility(item_id, facility_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item or facility not found")
    return result.to_dict()


@app.get("/surplus/{item_id}/{facility_id}")
def surplus_endpoint(item_id: str, facility_id: str):
    """Ranked list of surplus candidates for an item near a facility."""
    facility = get_facility(facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    
    item = get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    surpluses = find_surplus_facilities(item_id, facility_id)
    return {
        "item_id": item_id,
        "item_name": item["item_name"],
        "requesting_facility_id": facility_id,
        "candidates": [s.to_dict() for s in surpluses],
    }


@app.get("/transfer/recommend")
@app.post("/transfer/recommend")
def transfer_recommend(item_id: str, facility_id: str):
    """Full recommendation: surplus match + cascade check."""
    rec = recommend_transfer(item_id, facility_id)
    if not rec:
        return {"recommendation": None, "message": "No safe transfer found"}
    return {"recommendation": rec.to_dict()}


@app.post("/transfer/apply")
def transfer_apply(request: TransferApplyRequest):
    """Mark a recommended transfer as applied (updates mock stock)."""
    # Verify the transfer makes sense
    rec = recommend_transfer(request.item_id, request.destination_facility_id)
    if not rec:
        raise HTTPException(status_code=400, detail="No valid recommendation for this transfer")
    
    if rec.source_facility_id != request.source_facility_id:
        raise HTTPException(status_code=400, detail="Source facility doesn't match recommendation")
    
    if rec.quantity != request.quantity:
        raise HTTPException(status_code=400, detail="Quantity doesn't match recommendation")
    
    # Apply the transfer
    success = apply_transfer(rec)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to apply transfer")
    
    # Return updated forecasts for both facilities
    return {
        "success": True,
        "transfer_id": f"TXN_{request.item_id}_{request.source_facility_id}_{request.destination_facility_id}",
        "requester_forecast": forecast_item_at_facility(request.item_id, request.destination_facility_id).to_dict(),
        "donor_forecast": forecast_item_at_facility(request.item_id, request.source_facility_id).to_dict(),
    }


@app.post("/simulate")
def simulate_endpoint(request: SimulateRequest):
    """Run a disruption scenario, return before/after risk."""
    result = simulate_disruption(request.item_id, request.facility_id, request.delay_days)
    if not result:
        raise HTTPException(status_code=404, detail="Item or facility not found")
    return result.to_dict()


# Gemini explanation endpoint - uses real Gemini API
@app.post("/explain")
def explain_endpoint(request: ExplainRequest):
    """Gemini plain-language explanation of a given result."""
    try:
        model = genai.GenerativeModel('gemini-3.8-flash')
        
        if not request.recommended_transfer:
            prompt = (
                f"System: You are explaining a supply-chain risk result to a healthcare "
                f"facility administrator in plain, non-technical language. Use the "
                f"provided data only. Do not speculate beyond it. Keep it to 2-3 sentences.\n\n"
                f"Data:\n"
                f"{{\n"
                f'  "facility": "{request.facility}",\n'
                f'  "item": "{request.item}",\n'
                f'  "days_remaining": {request.days_remaining},\n'
                f'  "risk_level": "{request.risk_level}",\n'
                f'  "recommended_transfer": null\n'
                f"}}\n\n"
                f"Task: Explain why this facility is at risk and what actions might help."
            )
        else:
            rt = request.recommended_transfer
            prompt = (
                f"System: You are explaining a supply-chain risk result to a healthcare "
                f"facility administrator in plain, non-technical language. Use the "
                f"provided data only. Do not speculate beyond it. Keep it to 2-3 sentences.\n\n"
                f"Data:\n"
                f"{{\n"
                f'  "facility": "{request.facility}",\n'
                f'  "item": "{request.item}",\n'
                f'  "days_remaining": {request.days_remaining},\n'
                f'  "risk_level": "{request.risk_level}",\n'
                f'  "recommended_transfer": {{\n'
                f'    "from_facility": "{rt.get("from_facility", "A nearby facility")}",\n'
                f'    "quantity": {rt.get("quantity", 0)},\n'
                f'    "distance_km": {rt.get("distance_km", 0):.1f}\n'
                f'  }},\n'
                f'  "post_transfer_days_remaining": {request.post_transfer_days_remaining}\n'
                f"}}\n\n"
                f"Task: Explain why this facility is at risk and what the recommended "
                f"action would do."
            )
        
        response = model.generate_content(prompt)
        return {"explanation": response.text.strip()}
    
    except Exception as e:
        # Fallback to template if Gemini fails
        if not request.recommended_transfer:
            return {
                "explanation": (
                    f"{request.facility}'s {request.item} will run out in "
                    f"{request.days_remaining:.1f} days at current usage. "
                    f"This is {request.risk_level} risk — no transfer recommendation available yet."
                )
            }
        
        rt = request.recommended_transfer
        return {
            "explanation": (
                f"{request.facility}'s {request.item} will run out in "
                f"{request.days_remaining:.1f} days at current usage. "
                f"{rt.get('from_facility', 'A nearby facility')}, "
                f"{rt.get('distance_km', 0):.1f} km away, has enough surplus to safely transfer "
                f"{rt.get('quantity', 0)} units — this would extend {request.facility}'s supply "
                f"to roughly {request.post_transfer_days_remaining:.1f} days without creating "
                f"a new shortage at the donor facility."
            )
        }


# Health check
@app.get("/health")
def health():
    return {"status": "ok"}


# Reset data endpoint (for demo purposes)
@app.post("/admin/reset")
def reset_data():
    """Reset all data to initial seed state."""
    from core import load_data
    load_data()
    return {"status": "ok", "message": "Data reset to initial seed state"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)