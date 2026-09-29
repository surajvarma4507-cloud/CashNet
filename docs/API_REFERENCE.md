# CASHNET REST API Reference Manual

> **Smart India Hackathon (SIH26184)**  
> **AI-Powered Cybercrime Cash-Out Prediction & Investigator Decision-Support Platform**  
> **Documentation Version**: 2.0  
> **Base URL**: `http://localhost:8000`  
> **API Version Prefix**: `/api/v1`

---

## 1. General API Conventions

### Headers
- `Content-Type: application/json` (Required for POST requests)
- `Accept: application/json`

### Standard HTTP Status Codes
| Status Code | Description | Meaning in CASHNET |
|:---:|---|---|
| `200 OK` | Success | Request succeeded; response contains requested data |
| `201 Created` | Created | Resource successfully created (e.g. Action logging) |
| `400 Bad Request` | Client Error | Invalid parameter combinations or validation failure |
| `404 Not Found` | Not Found | Target case, account, location, or prediction record does not exist |
| `422 Unprocessable Entity` | Schema Error | Pydantic validation error (e.g. invalid date format or out-of-range value) |
| `500 Internal Server Error` | Server Error | Unhandled backend exception |

### Point-in-Time Parameters
Most investigative endpoints accept point-in-time parameters:
- `as_of` (ISO-8601 string, optional): Evaluates the query state as of this timestamp. Default: `complaint_registered_at`.
- `snapshot_id` (string, optional): Specific precomputed feature snapshot ID to reference.

---

## 2. System & Health Endpoints

### 2.1 Root Health Check
- **Route**: `GET /health`
- **Description**: Quick liveness probe.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "app_name": "CASHNET",
  "version": "0.1.0"
}
```
- **Example `curl`**:
```bash
curl -s http://localhost:8000/health
```

---

### 2.2 Detailed System & Database Diagnostics
- **Route**: `GET /api/v1/health`
- **Description**: Comprehensive health check verifying database connectivity, live table record counts, and ML subsystem readiness.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "database": {
    "status": "connected",
    "table_counts": {
      "locations": 300,
      "accounts": 10001,
      "complaints": 5000,
      "transactions": 65420,
      "cashout_events": 6997,
      "prediction_snapshots": 5000,
      "prediction_records": 12
    }
  },
  "ml_service": {
    "status": "ready",
    "model_a_loaded": true,
    "model_c_loaded": true,
    "model_b_strategy": "fallback_distance_baseline"
  }
}
```
- **Example `curl`**:
```bash
curl -s http://localhost:8000/api/v1/health
```

---

## 3. Case Management & Investigation Endpoints

### 3.1 List Cases (Filterable & Paginated)
- **Route**: `GET /api/v1/cases`
- **Query Parameters**:
  - `skip` (integer, default: 0): Pagination offset.
  - `limit` (integer, default: 20, max: 100): Page size.
  - `status` (string, optional): Filter by case status (`active`, `closed`, `under_investigation`).
  - `category` (string, optional): Filter by fraud category (e.g. `UPI_FRAUD`, `INVESTMENT_SCAM`).
  - `min_amount` (number, optional): Minimum defrauded amount.
  - `max_amount` (number, optional): Maximum defrauded amount.
  - `sort_by` (string, default: `complaint_registered_at`): Sort field.
  - `sort_order` (string, default: `desc`): `asc` or `desc`.
- **Response `200 OK`**:
```json
{
  "total": 5000,
  "skip": 0,
  "limit": 20,
  "items": [
    {
      "case_id": "CASE_000001",
      "victim_account_id": "ACC_000042",
      "amount": 75000.0,
      "category": "UPI_FRAUD",
      "status": "under_investigation",
      "fraud_occurred_at": "2024-01-15T08:30:00Z",
      "complaint_registered_at": "2024-01-15T09:15:00Z",
      "victim_name": "Rohan Sharma",
      "victim_phone": "+91-9876543210"
    }
  ]
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/cases?limit=5&category=UPI_FRAUD"
```

---

### 3.2 Get Case Dossier
- **Route**: `GET /api/v1/cases/{case_id}`
- **Query Parameters**:
  - `as_of` (string, optional): ISO-8601 timestamp cutoff.
- **Response `200 OK`**:
```json
{
  "case_id": "CASE_000001",
  "complaint": {
    "case_id": "CASE_000001",
    "victim_account_id": "ACC_000042",
    "amount": 75000.0,
    "category": "UPI_FRAUD",
    "status": "under_investigation",
    "fraud_occurred_at": "2024-01-15T08:30:00Z",
    "complaint_registered_at": "2024-01-15T09:15:00Z"
  },
  "victim_account": {
    "account_id": "ACC_000042",
    "bank_name": "State Bank of India",
    "account_type": "SAVINGS",
    "home_branch_location_id": "LOC_000012",
    "account_age_days": 1420
  },
  "summary_metrics": {
    "total_flow_amount": 75000.0,
    "observed_hops": 3,
    "participating_accounts_count": 5,
    "actions_count": 1
  }
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/cases/CASE_000001"
```

---

### 3.3 Get Case Transactions (Money Trail Ledger)
- **Route**: `GET /api/v1/cases/{case_id}/transactions`
- **Query Parameters**:
  - `as_of` (string, optional): ISO-8601 timestamp cutoff.
- **Response `200 OK`**:
```json
{
  "case_id": "CASE_000001",
  "total_transactions": 4,
  "transactions": [
    {
      "transaction_id": "TX_000101",
      "from_account_id": "ACC_000042",
      "to_account_id": "ACC_000105",
      "amount": 75000.0,
      "payment_channel": "UPI",
      "completed_at": "2024-01-15T08:35:00Z"
    },
    {
      "transaction_id": "TX_000102",
      "from_account_id": "ACC_000105",
      "to_account_id": "ACC_000210",
      "amount": 50000.0,
      "payment_channel": "IMPS",
      "completed_at": "2024-01-15T08:42:00Z"
    }
  ]
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/cases/CASE_000001/transactions"
```

---

### 3.4 Get Participating Accounts with Assigned Roles
- **Route**: `GET /api/v1/cases/{case_id}/accounts`
- **Description**: Returns all accounts participating in the case money trail with computed topological roles.
- **Response `200 OK`**:
```json
{
  "case_id": "CASE_000001",
  "accounts": [
    {
      "account_id": "ACC_000042",
      "role": "victim",
      "hop_depth": 0,
      "bank_name": "State Bank of India",
      "account_type": "SAVINGS",
      "is_flagged_mule": false
    },
    {
      "account_id": "ACC_000105",
      "role": "mule_hop_1",
      "hop_depth": 1,
      "bank_name": "HDFC Bank",
      "account_type": "SAVINGS",
      "is_flagged_mule": true
    }
  ]
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/cases/CASE_000001/accounts"
```

---

### 3.5 Reconstruct Multi-Hop Money Trail
- **Route**: `GET /api/v1/cases/{case_id}/money-trail`
- **Query Parameters**:
  - `as_of` (string, optional): ISO-8601 cutoff.
  - `max_hops` (integer, default: 10): Maximum BFS traversal depth.
- **Response `200 OK`**:
```json
{
  "case_id": "CASE_000001",
  "max_hop_depth": 3,
  "total_nodes": 5,
  "total_edges": 4,
  "has_cycle": false,
  "cycles_detected": [],
  "disconnected_links": [],
  "nodes": [
    { "id": "ACC_000042", "label": "Victim", "hop": 0, "role": "victim" },
    { "id": "ACC_000105", "label": "Layer 1 Mule", "hop": 1, "role": "mule_hop_1" }
  ],
  "edges": [
    {
      "from": "ACC_000042",
      "to": "ACC_000105",
      "amount": 75000.0,
      "channel": "UPI",
      "completed_at": "2024-01-15T08:35:00Z"
    }
  ]
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/cases/CASE_000001/money-trail"
```

---

### 3.6 Get Visual Graph Payload
- **Route**: `GET /api/v1/cases/{case_id}/graph`
- **Description**: Returns Cytoscape/Vis.js compatible node-link payload formatted for immediate UI rendering.
- **Response `200 OK`**:
```json
{
  "case_id": "CASE_000001",
  "elements": {
    "nodes": [
      { "data": { "id": "ACC_000042", "label": "Victim (ACC_000042)", "type": "victim", "in_degree": 0, "out_degree": 1 } },
      { "data": { "id": "ACC_000105", "label": "Mule (ACC_000105)", "type": "mule", "in_degree": 1, "out_degree": 2 } }
    ],
    "edges": [
      { "data": { "id": "TX_000101", "source": "ACC_000042", "target": "ACC_000105", "label": "₹75,000 (UPI)" } }
    ]
  },
  "topology": {
    "density": 0.20,
    "is_acyclic": true,
    "connected_components": 1
  }
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/cases/CASE_000001/graph"
```

---

### 3.7 Get Cross-Case Syndicate Network Intelligence
- **Route**: `GET /api/v1/cases/{case_id}/network`
- **Description**: Identifies shared mule accounts and cross-case syndicate clusters.
- **Response `200 OK`**:
```json
{
  "case_id": "CASE_000001",
  "shared_accounts_count": 2,
  "linked_cases_count": 4,
  "syndicate_cluster_id": "SYN_000012",
  "total_syndicate_volume": 420000.0,
  "shared_accounts": [
    {
      "account_id": "ACC_000105",
      "co_occurring_case_ids": ["CASE_000001", "CASE_000312", "CASE_000845"],
      "total_cross_case_inflow": 250000.0
    }
  ]
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/cases/CASE_000001/network"
```

---

### 3.8 Get Related Cases
- **Route**: `GET /api/v1/cases/{case_id}/related-cases`
- **Query Parameters**:
  - `skip` (integer, default: 0)
  - `limit` (integer, default: 10)
- **Response `200 OK`**:
```json
{
  "case_id": "CASE_000001",
  "total_related": 2,
  "items": [
    {
      "case_id": "CASE_000312",
      "shared_account_id": "ACC_000105",
      "category": "INVESTMENT_SCAM",
      "amount": 120000.0,
      "complaint_registered_at": "2024-01-14T11:00:00Z"
    }
  ]
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/cases/CASE_000001/related-cases"
```

---

### 3.9 Record Investigator Action (Append-Only)
- **Route**: `POST /api/v1/cases/{case_id}/actions`
- **Request Body**:
```json
{
  "action_type": "account_freeze",
  "notes": "Emergency 1930 notice issued to HDFC Nodal Officer for ACC_000105",
  "performed_by": "IO_Inspector_Rajesh",
  "action_status": "executed"
}
```
- **Response `201 Created`**:
```json
{
  "action_id": "ACT_000018",
  "case_id": "CASE_000001",
  "action_type": "account_freeze",
  "notes": "Emergency 1930 notice issued to HDFC Nodal Officer for ACC_000105",
  "performed_by": "IO_Inspector_Rajesh",
  "action_status": "executed",
  "created_at": "2026-09-28T14:20:00Z"
}
```
- **Example `curl`**:
```bash
curl -s -X POST "http://localhost:8000/api/v1/cases/CASE_000001/actions" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "account_freeze", "notes": "Freeze notice sent", "performed_by": "IO_Rajesh", "action_status": "executed"}'
```

---

## 4. Account Intelligence Endpoints

### 4.1 Get Account Network Profile
- **Route**: `GET /api/v1/accounts/{account_id}/network`
- **Response `200 OK`**:
```json
{
  "account_id": "ACC_000105",
  "bank_name": "HDFC Bank",
  "account_type": "SAVINGS",
  "total_cases_participated": 3,
  "total_inflow": 250000.0,
  "total_outflow": 240000.0,
  "is_flagged_mule": true,
  "co_occurring_accounts": ["ACC_000042", "ACC_000210", "ACC_000998"]
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/accounts/ACC_000105/network"
```

---

### 4.2 Get Account Money Trails
- **Route**: `GET /api/v1/accounts/{account_id}/money-trails`
- **Response `200 OK`**:
```json
{
  "account_id": "ACC_000105",
  "participating_trails": [
    {
      "case_id": "CASE_000001",
      "role": "mule_hop_1",
      "hop_depth": 1,
      "incoming_amount": 75000.0,
      "outgoing_amount": 50000.0
    }
  ]
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/accounts/ACC_000105/money-trails"
```

---

## 5. Location & GIS Endpoints

### 5.1 List Locations (with Spatial Radius Query)
- **Route**: `GET /api/v1/locations`
- **Query Parameters**:
  - `latitude` (float, optional): Center latitude in degrees ($6.0$ to $38.0$).
  - `longitude` (float, optional): Center longitude in degrees ($68.0$ to $98.0$).
  - `radius_km` (float, default: 10.0, max: 100.0): Search radius.
  - `city` (string, optional): Filter by city name (e.g. `Mumbai`, `Delhi`, `Bengaluru`).
  - `terminal_type` (string, optional): `ATM`, `BRANCH`, or `CSP_KIOSK`.
  - `limit` (integer, default: 50)
- **Response `200 OK`**:
```json
{
  "total": 12,
  "items": [
    {
      "location_id": "LOC_000012",
      "bank_name": "State Bank of India",
      "terminal_type": "ATM",
      "address": "Andheri East Station Road",
      "city": "Mumbai",
      "state": "Maharashtra",
      "latitude": 19.1197,
      "longitude": 72.8468,
      "distance_km": 1.42
    }
  ]
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/locations?latitude=19.12&longitude=72.85&radius_km=5"
```

---

### 5.2 Get Location by ID
- **Route**: `GET /api/v1/locations/{location_id}`
- **Response `200 OK`**:
```json
{
  "location_id": "LOC_000012",
  "bank_name": "State Bank of India",
  "terminal_type": "ATM",
  "address": "Andheri East Station Road",
  "city": "Mumbai",
  "state": "Maharashtra",
  "latitude": 19.1197,
  "longitude": 72.8468,
  "historical_cashout_count": 34
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/locations/LOC_000012"
```

---

### 5.3 List Location Spatial Clusters
- **Route**: `GET /api/v1/locations/clusters`
- **Query Parameters**:
  - `city` (string, optional): Filter clusters by city name (e.g., `Mumbai`, `Delhi`).
- **Response `200 OK`**:
```json
{
  "total_clusters": 12,
  "items": [
    {
      "area_cluster_id": "CLUSTER_MUM_01",
      "cluster_name": "South Mumbai Financial Hub",
      "city": "Mumbai",
      "region": "Maharashtra",
      "center_latitude": 18.9388,
      "center_longitude": 72.8354,
      "total_locations": 25,
      "atm_count": 18,
      "branch_count": 5,
      "kiosk_count": 2,
      "observed_cashout_events_count": 12,
      "total_observed_cashout_volume": 450000.0
    }
  ]
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/locations/clusters?city=Mumbai"
```

---

### 5.4 List Location Cash-Out Hotspots
- **Route**: `GET /api/v1/locations/hotspots`
- **Description**: Returns top physical extraction points ranked by observed historical cashout frequency (strictly excludes future ground-truth).
- **Query Parameters**:
  - `city` (string, optional): Filter by city.
  - `limit` (integer, default: 20): Maximum hotspots to return.
  - `min_cashouts` (integer, default: 1): Minimum observed cashouts threshold.
- **Response `200 OK`**:
```json
{
  "total_hotspots": 20,
  "items": [
    {
      "location_id": "LOC_MUM_ATM_001",
      "location_name": "State Bank ATM - Nariman Point",
      "location_type": "atm",
      "city": "Mumbai",
      "region": "Maharashtra",
      "latitude": 18.9256,
      "longitude": 72.8242,
      "area_cluster_id": "CLUSTER_MUM_01",
      "observed_cashout_count": 9,
      "total_observed_cashout_volume": 380000.0,
      "activity_risk_level": "high"
    }
  ]
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/locations/hotspots?city=Mumbai&limit=10"
```

---

## 6. Machine Learning & Decision Support Endpoints

### 6.1 Generate Point-in-Time Prediction & Narrative
- **Route**: `POST /api/v1/cases/{case_id}/predictions`
- **Query Parameters**:
  - `as_of` (string, optional): ISO-8601 timestamp cutoff.
  - `snapshot_id` (string, optional): Precomputed snapshot reference.
- **Request Body** (optional):
```json
{
  "notes": "Triggered by IO for tactical deployment"
}
```
- **Response `200 OK`**:
```json
{
  "prediction_id": "PRED_000045",
  "case_id": "CASE_000001",
  "occurrence_prediction": {
    "probability": 0.884,
    "risk_tier": "CRITICAL",
    "threshold_used": 0.85,
    "model_name": "RandomForestClassifier",
    "model_version": "occurrence_baseline_v1"
  },
  "candidate_locations": {
    "strategy_used": "fallback_distance_baseline",
    "ml_ranker_status": "REJECTED_SYNTHETIC_CANDIDATE_ARTIFACT",
    "total_candidates": 7,
    "ranked_locations": [
      {
        "rank": 1,
        "location_id": "LOC_000012",
        "bank_name": "State Bank of India",
        "terminal_type": "ATM",
        "city": "Mumbai",
        "distance_from_account_km": 1.42,
        "historical_cashout_count": 34
      }
    ]
  },
  "timing_prediction": {
    "estimated_minutes_until_cashout": 44.5,
    "model_status": "EXPERIMENTAL_BASELINE",
    "uncertainty_note": "High variance: uniform synthetic delay distribution (MAE ~41.8 min)"
  },
  "decision_support_narrative": {
    "summary": "Case exhibits CRITICAL cash-out risk (88.4% probability) with rapid layered dispersion.",
    "risk_factors": [
      "Layer 1 funds split into multiple secondary accounts within 12 minutes.",
      "Identified 1 known high-risk synthetic mule account in money trail.",
      "Cross-case link detected with 2 prior registered cybercrime complaints."
    ],
    "protective_factors": [],
    "recommended_actions": [
      "Issue urgent Section 91 CrPC notice to HDFC Bank for ACC_000105.",
      "Dispatch tactical surveillance alert to Mumbai Police patrol near ATM LOC_000012."
    ]
  },
  "provenance": {
    "features_count": 26,
    "as_of_timestamp": "2024-01-15T09:15:00Z",
    "created_at": "2026-09-28T14:25:00Z"
  }
}
```
- **Example `curl`**:
```bash
curl -s -X POST "http://localhost:8000/api/v1/cases/CASE_000001/predictions"
```

---

### 6.2 List Prediction Execution History for a Case
- **Route**: `GET /api/v1/cases/{case_id}/predictions`
- **Response `200 OK`**:
```json
{
  "case_id": "CASE_000001",
  "total_predictions": 1,
  "items": [
    {
      "prediction_id": "PRED_000045",
      "occurrence_probability": 0.884,
      "risk_tier": "CRITICAL",
      "created_at": "2026-09-28T14:25:00Z"
    }
  ]
}
```
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/cases/CASE_000001/predictions"
```

---

### 6.3 Retrieve Immutable Prediction Record by ID
- **Route**: `GET /api/v1/predictions/{prediction_id}`
- **Response `200 OK`**: Complete persisted audit record including full feature map, candidate locations, and serialized narrative.
- **Example `curl`**:
```bash
curl -s "http://localhost:8000/api/v1/predictions/PRED_000045"
```

---

**Last Updated**: 2026-09-28  
**Documentation Version**: 2.0  
**Status**: Complete REST API Specification
