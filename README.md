# StockPulse — Medicine & Vaccine Stockout Prevention

End-to-end prototype for predicting medicine/vaccine stockouts and recommending inter-facility transfers to prevent them.

## Architecture

```
Frontend (React + Vite) → Backend (FastAPI) → Data Layer (JSON/In-memory)
```

## Features Implemented

### 1. Data Layer (`backend/seed_data.py`)
- 5 real facilities in Madurai district (real lat/long coordinates)
- 3 items: ORS (fast-moving), Measles Vaccine, Paracetamol (slow-moving control)
- 14 days of consumption history per facility/item
- 1 disruption scenario: 3-day supplier delay for ORS at PHC_01

### 2. Core Algorithms (`backend/core.py`)
- **Runway Forecast**: Days remaining = stock / 7-day avg consumption
- **Risk Levels**: critical (< lead time), watch (< 1.5× lead time), normal
- **Surplus Matcher**: Finds nearby facilities with >2× lead time buffer
- **Cascade Check**: Ensures donor stays safe after transfer (≥ lead time days)
- **Transfer Recommendation**: Combines surplus match + cascade check
- **Disruption Simulation**: Recomputes risk with extended lead time

### 3. API Endpoints (`backend/main.py`)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/facilities` | GET | List all facilities with risk summary |
| `/facilities/{id}/stock` | GET | Stock + runway for all items at facility |
| `/forecast/{item}/{facility}` | GET | Runway + risk for one item |
| `/surplus/{item}/{facility}` | GET | Ranked surplus candidates |
| `/transfer/recommend` | POST | Full recommendation (surplus + cascade) |
| `/transfer/apply` | POST | Apply transfer, update mock stock |
| `/simulate` | POST | Run disruption scenario |
| `/explain` | POST | Plain-language explanation |
| `/admin/reset` | POST | Reset data to seed state (demo) |

### 4. Frontend Screens (`frontend/stockpulse-ui/`)
- **Screen 1 - Facility Overview**: Grid of facilities with per-item risk badges
- **Screen 2 - Facility Detail**: Item list with runway bars, simulate/recommend buttons
- **Screen 3 - Recommendation Panel**: Transfer details with Explain/Apply actions
- **Screen 4 - Gemini Query**: Free-text questions (uses `/explain` endpoint)

## Quick Start

### Backend
```bash
cd backend
python seed_data.py        # Generate mock data
python main.py             # Start API on http://localhost:8000
```

### Frontend
```bash
cd frontend/stockpulse-ui
npm install
npm run dev                # Start on http://localhost:5175
```

## Demo Script

1. **Open http://localhost:5175** — Facility Overview loads
2. **See PHC Madurai North (PHC_01)** — Red "critical" badge for ORS
3. **Click PHC_01** — Facility Detail shows ORS at 1.3 days remaining
4. **Click "Simulate 3-Day Delay"** — Risk stays critical, lead time 3→6 days
5. **Click "Get Transfer Recommendation"** — Panel shows PHC Melur (25.8km) can send 142 units
6. **Click "Explain"** — AI-generated plain-language explanation
7. **Click "Apply Transfer"** — PHC_01 ORS goes to 6 days (normal), PHC_04 stays safe at 67 days
8. **Click "Reset" (or call `/admin/reset`)** — Returns to initial state

## Key Numbers (Seed Data)

| Facility | Item | Stock | Daily Avg | Days Remaining | Lead Time | Risk |
|----------|------|-------|-----------|----------------|-----------|------|
| PHC_01 | ORS | 40 | 30.4 | **1.3** | 3 | **critical** |
| PHC_04 | ORS | 500 | 5.3 | 94.6 | 3 | normal (surplus donor) |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, TypeScript |
| Backend | FastAPI, Uvicorn |
| Data | JSON files + in-memory dicts |
| Geo | Haversine formula (no external API) |
| AI | Gemini API template (placeholder) |

## Design Principles

- **Transparent formulas**: Every number explainable in one sentence
- **No ML**: Simple moving averages, no hidden logic
- **Cascade safety**: Donor facility protection is core novelty
- **Mock data**: Hand-authored for reliable demo, not randomized

## What's NOT Built (Intentional Cuts)

- Real DVDMS/eVIN integration
- ML/trained models
- Doctor/lab scheduling
- Multi-district dashboards
- User authentication
- Offline sync
- IoT/cold-chain sensors

---

**Built for Track 3: Smart Health & Supply Chain Resilience**