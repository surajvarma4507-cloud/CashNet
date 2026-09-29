# CASHNET Demonstration Guide

> **Smart India Hackathon (SIH26184)**
> **AI-Powered Cybercrime Cash-Out Prediction & Investigator Decision-Support Platform**

---

## 1. Project Purpose

CASHNET assists law enforcement agencies (LEAs) in tracking money-laundering trails across multi-hop mule account networks and prioritizing high-probability physical cash withdrawal locations (ATMs, bank branches, CSP kiosks) to enable rapid intervention before funds are extracted.

**Key Capabilities:**
- Multi-hop money trail reconstruction with cycle detection
- Cross-case syndicate network analysis
- ML-powered cash-out occurrence prediction
- Distance-based candidate location ranking
- Interactive GIS visualization
- Immutable investigator action audit logging

**Important Disclaimers:**
- All data is **synthetic** - no real bank accounts, transactions, or individuals
- Predictions are **advisory only** - human review required before action
- System does **not** automatically freeze accounts or dispatch personnel
- Evaluation metrics are from synthetic data only

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                   │
│  Dashboard │ Cases │ Dossier │ Money Trail │ GIS │ Predictions  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/JSON
┌────────────────────────────▼────────────────────────────────────┐
│                     BACKEND (FastAPI + SQLAlchemy 2.0)          │
│   Health │ Cases │ Transactions │ Money Trail │ Network │ ML    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              DATABASE (SQLite dev / PostgreSQL prod)            │
│   13 Tables │ 5,000 Cases │ 10,001 Accounts │ 65,000+ Txns     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Application Startup

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)
- SQLite (included with Python)

### Quick Start Commands

```bash
# 1. Navigate to project directory
cd /home/Jarvis/Downloads/Dataset

# 2. Install backend dependencies (if not already installed)
pip install -r requirements.txt

# 3. Apply database migrations
python3 -m alembic upgrade head

# 4. Import synthetic data (if database is empty)
python3 scripts/import_data.py --wipe

# 5. Start backend server
python3 -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

# 6. In a new terminal, start frontend
cd src/frontend
npm install  # if not already installed
npm run dev

# 7. Access the application
# Backend API: http://localhost:8000/docs
# Frontend: http://localhost:5173
```

### Production Build

```bash
# Build frontend for production
npm --prefix src/frontend run build

# Serve production build
npm --prefix src/frontend run preview
```

---

## 4. Demonstration Scenarios

### Scenario A: Multi-Hop Financial Trail

**Case ID:** `CASE_2026_003040`

**Selection Rationale:** High-value case (₹49.5L) with multi-hop transaction chain and future cash-out target for evaluation demonstration.

**Expected Workflow:**
1. Open case registry at `http://localhost:5173`
2. Search for `CASE_2026_003040` in the case list
3. Click to open the case dossier
4. Review complaint details (fraud type, amount, timestamps)
5. Navigate to "Money Trail" tab to view transaction graph
6. Observe hop-depth indexing and transaction flow arrows
7. Check for cycle detection (if present)
8. Review connected accounts and their roles

**Expected Behavior:**
- Transaction timeline shows chronological flow
- Money trail graph displays nodes (accounts) and edges (transactions)
- Hop levels indicate distance from victim source
- Cycle detection highlights any circular fund movements
- Empty state handled gracefully if no transactions

---

### Scenario B: Candidate Cash-Out Location Prediction

**Case ID:** `CASE_2026_004961`

**Selection Rationale:** High-value case with future cash-out target, suitable for demonstrating ML prediction and location ranking.

**Expected Workflow:**
1. Open case `CASE_2026_004961`
2. Navigate to "AI Prediction" tab
3. Click "Generate Prediction" button
4. Review occurrence probability and risk tier
5. Examine ranked candidate ATM locations
6. Note distance calculations and historical cashout counts
7. Review timing estimate (with high-uncertainty disclaimer)
8. Read narrative explanation with risk/protective factors
9. Click on top candidate location to view in GIS

**Expected Behavior:**
- Model A outputs probability (0-1) and risk tier (Low/Moderate/High/Critical)
- Model B (distance fallback) ranks candidates by proximity
- Model C provides timing window with uncertainty disclaimer
- Explanation includes actionable recommendations
- Advisory disclaimer clearly visible

**Key Disclaimers:**
- "Predictions are advisory only"
- "Model C is experimental baseline with high uncertainty"
- "Distance fallback active (learned ranker rejected due to artifact)"

---

### Scenario C: No Future Cash-Out Target

**Case ID:** `CASE_2026_001532`

**Selection Rationale:** High-value case with observed cash-outs but no future ground-truth target, demonstrating that the system does not invent predictions.

**Expected Workflow:**
1. Open case `CASE_2026_001532`
2. Review transaction history and cash-out events
3. Navigate to "AI Prediction" tab
4. Observe that prediction still computes probability
5. Note that historical cashouts are shown
6. Understand distinction: prediction is probability, not confirmed event

**Expected Behavior:**
- System computes occurrence probability based on features
- Does NOT claim certainty about future cash-out
- Historical cash-outs clearly labeled as "observed"
- Prediction output clearly labeled as "model inference"
- No fabricated future events

**Key Learning:**
- Predictions ≠ Confirmations
- Model outputs probability, not guarantee
- Human investigator must interpret results

---

### Scenario D: Investigator Action & Audit Trail

**Case ID:** `CASE_2026_001532` (or any case)

**Expected Workflow:**
1. Open a case dossier
2. Navigate to "Actions" tab
3. Click "Record Action" button
4. Select action type: "Account Freeze Request", "Field Alert", "Surveillance Request", or "Note"
5. Enter case notes and justification
6. Submit the action
7. Observe success toast notification
8. Verify action appears in audit timeline
9. Note that actions cannot be edited or deleted

**Expected Behavior:**
- Action recorded with unique ID
- Timestamp automatically captured
- Investigator ID recorded
- Action appears in immutable audit log
- Clear notice: "Action recorded to local audit log only"

**Key Safeguards:**
- Actions are **record-only** - no automatic external dispatch
- Audit log is append-only (protected by ORM listeners)
- System does NOT contact external services
- Human authorization required for real-world action

---

## 5. GIS Visualization Demo

**Expected Workflow:**
1. From case dossier, click on a candidate location
2. Or navigate to "Locations" tab in main navigation
3. Explore the interactive map with 300+ terminals
4. Use radius preset buttons (5km, 10km, 25km)
5. Toggle layers: Terminals, Clusters, Hotspots
6. Click on terminal markers for details
7. Use "Center Radius Query" to set anchor point
8. Observe concentric radius rings on map
9. Click "Log Tactical Alert" from terminal card

**Expected Behavior:**
- Map renders all 300 synthetic terminal locations
- Zoom/pan controls functional
- Radius rings update dynamically
- Cluster bubbles show terminal counts
- Hotspot markers indicate high-activity locations
- Tactical alerts record to audit log

---

## 6. Controlled Evaluation Reveal

The evaluation metrics are computed on the held-out ground-truth table (`prediction_ground_truth`), which is **strictly isolated** from operational endpoints.

### Running Evaluation

```bash
python3 scripts/compute_evaluation_metrics.py
```

### Sample Results (from actual execution)

**Model A - Occurrence Classifier:**
- Accuracy: 63.5%
- ROC-AUC: 0.766
- PR-AUC: 0.669
- Recall: 92.7% (high sensitivity to catch potential cash-outs)

**Model B - Location Ranking (Distance Fallback):**
- Top-1 Accuracy: 69.9%
- Top-3 Accuracy: 70.9%
- Top-5 Accuracy: 72.5%

**Model C - Timing Regressor:**
- MAE: 42.3 minutes
- Baseline MAE: 43.8 minutes
- **Note:** High uncertainty due to uniform random delays in synthetic generator

**Important:**
- Evaluation data is **never** exposed through operational APIs
- Ground-truth table is isolated from case dossier endpoints
- Metrics are from synthetic data only - not real-world performance

---

## 7. Known Limitations

1. **Synthetic Data Only**: All records are generated prototypes
2. **No Authentication**: Prototype lacks RBAC - not for production use
3. **No Real-Time Updates**: Polling-based, not WebSocket
4. **Model B Rejection**: Learned ranker rejected due to synthetic artifact
5. **Model C Uncertainty**: Timing estimates have high variance
6. **Local Actions Only**: No external integrations (bank APIs, police dispatch)
7. **Append-Only Audit**: Protected by ORM listeners; direct SQL could bypass
8. **CORS Open**: Allows all origins in development mode

---

## 8. Responsible Use Safeguards

- **No autonomous action**: System records decisions; humans execute
- **Advisory predictions**: All ML outputs require human interpretation
- **Ground-truth isolation**: Evaluation data never leaks to operations
- **Clear disclaimers**: UI labels distinguish prediction from observation
- **Audit trail**: All investigator actions logged immutably
- **Synthetic labels**: No real individuals marked as "guilty"

---

## 9. Demonstration Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads and displays dashboard
- [ ] Case list populates with synthetic data
- [ ] Case dossier opens with all tabs functional
- [ ] Money trail graph renders correctly
- [ ] Prediction generates with explanation
- [ ] GIS map displays terminals and radius overlays
- [ ] Investigator action records successfully
- [ ] Action appears in audit timeline
- [ ] No ground-truth data in operational views

---

## 10. Troubleshooting

**Backend won't start:**
- Check Python version: `python3 --version` (need 3.11+)
- Install dependencies: `pip install -r requirements.txt`
- Check database: `python3 -m alembic current`

**Frontend won't start:**
- Check Node version: `node --version` (need 18+)
- Install dependencies: `npm --prefix src/frontend install`
- Check API URL in `src/frontend/src/api/client.ts`

**Database errors:**
- Reset database: `python3 scripts/import_data.py --wipe`
- Check migrations: `python3 -m alembic upgrade head`

**No data in frontend:**
- Verify backend is running on port 8000
- Check health endpoint: `curl http://localhost:8000/health`
- Verify database has records: `sqlite3 cashnet_dev.db "SELECT COUNT(*) FROM complaints"`

---

**Last Updated:** 2026-09-29
**Documentation Version:** 3.0
**Project Status:** Stage 6 Complete - Ready for Demonstration
