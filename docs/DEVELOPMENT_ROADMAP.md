# CASHNET Development Roadmap & Staged Implementation Plan

> **Smart India Hackathon (SIH26184)**  
> **AI-Powered Cybercrime Cash-Out Prediction & Investigator Decision-Support Platform**  
> **Documentation Version**: 2.0  
> **Last Verified**: 2026-09-28

---

## 1. Roadmap Overview & Milestone Timeline

CASHNET follows a phased, evidence-verified engineering methodology. Each stage requires full automated test suite passage and forensic verification before advancing to subsequent layers.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: Backend Foundation & Data Infrastructure              [ COMPLETE ] │
│ - FastAPI, SQLAlchemy 2.0 (13 Models), Alembic, CSV Importer                │
├─────────────────────────────────────────────────────────────────────────────┤
│ STAGE 2: Money Trail Reconstruction & Network Intelligence     [ COMPLETE ] │
│ - Multi-Hop BFS, 3-Color DFS Cycles, Anomaly Detection, Syndicates          │
├─────────────────────────────────────────────────────────────────────────────┤
│ STAGE 3: ML Prediction Service Integration                     [ COMPLETE ] │
│ - Model A (86.2% Acc), Model B (Distance Fallback), Model C, PredictionRec  │
├─────────────────────────────────────────────────────────────────────────────┤
│ STAGE 3.1: Prediction Integration Audit                        [ COMPLETE ] │
│ - Forensic Schema Consistency, Missing Artifact Fallbacks, Provenance Checks│
├─────────────────────────────────────────────────────────────────────────────┤
│ STAGE 4: Investigator Dashboard UI                             [ COMPLETE ] │
│ - React/TypeScript SPA, Case Triage, Graph Visualization, Action Logging    │
├─────────────────────────────────────────────────────────────────────────────┤
│ STAGE 5: Interactive GIS Map & Spatial Intelligence            [ COMPLETE ] │
│ - Coordinate Projection (300 ATMs), Concentric Radii, Clusters, Hotspots    │
├─────────────────────────────────────────────────────────────────────────────┤
│ STAGE 6: End-to-End Integration, Hardening & Demonstration     [ PLANNED ]  │
│ - Demo Scenarios, Docker Compose, Performance Profiling, SIH Submission     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Stage Specifications

### Stage 1: Backend Foundation & Data Infrastructure (COMPLETE)
- **Scope**: FastAPI core application, 13 SQLAlchemy ORM entities, Alembic migrations, CSV importer, CRUD endpoints, anti-leakage guards, append-only investigator audit.
- **Verification Status**: Fully verified. 47 automated tests passed.
- **Key Artifacts**:
  - `src/backend/main.py`, `src/backend/config.py`
  - `src/backend/db/models.py` (13 entities)
  - `src/backend/importer/data_importer.py`
  - `tests/test_backend_api.py`, `tests/test_data_leakage.py`

---

### Stage 2: Money Trail Reconstruction & Network Intelligence (COMPLETE)
- **Scope**: Multi-hop BFS traversal, deterministic hop indexing, 3-color DFS directed cycle detection, disconnected link flagging, cross-case shared mule analysis, syndicate clustering, account profiling.
- **Verification Status**: Fully verified. 71 automated tests passed.
- **Key Artifacts**:
  - `src/backend/services/money_trail_service.py`
  - `src/backend/services/network_service.py`
  - `tests/test_money_trail.py`, `tests/test_network_intelligence.py`

---

### Stage 3: ML Prediction Service Integration (COMPLETE)
- **Scope**: Feature assembly engine (26 strict features), Model A occurrence classifier, Model B distance fallback baseline, Model C timing regressor, structured narrative explanation synthesis, immutable `PredictionRecord` persistence.
- **Verification Status**: Fully verified. **80 automated tests passing** (verified on 2026-09-28).
- **Key Artifacts**:
  - `src/backend/services/prediction_service.py`
  - `src/backend/api/routes/predictions.py`
  - `models/occurrence_baseline.joblib`, `models/timing_baseline.joblib`, `models/feature_manifest_used.json`
  - `tests/test_prediction_service.py`

---

### Stage 3.1: Prediction Integration Audit (NEXT MILESTONE)
- **Objective**: Conduct an exhaustive pre-frontend forensic audit to ensure absolute stability, security, and schema contract adherence.
- **Acceptance Criteria**:
  1. All 26 feature extraction routines verified against raw database tables for edge cases (e.g., zero previous transactions, null amounts).
  2. Provenance metadata (`model_versions`, `features_used`) strictly validated on persisted `PredictionRecord` objects.
  3. Missing artifact fallback paths verified without raising uncaught server exceptions.
  4. Zero data leakage across all 18 API routes independently verified.
- **Deliverable**: `reports/stage_3_1_audit_report.md`.

---

### Stage 4: Investigator Dashboard UI (PLANNED)
- **Objective**: Build a high-performance, modern web application for law enforcement investigators and cybercrime analysts.
- **Proposed Technology Stack**:
  - **Framework**: React 18+ with TypeScript
  - **Build Tooling**: Vite
  - **Styling & UI Components**: Tailwind CSS + shadcn/ui or Radix UI
  - **Graph Visualization**: Cytoscape.js or Vis.js Network
  - **State Management & Data Fetching**: TanStack Query (React Query) + Axios
  - **Icons**: Lucide React
- **Target Views & Component Hierarchy**:
  1. **Case Triage Dashboard (`/cases`)**:
     - Filterable case queue sorted by risk score, complaint amount, and registration recency.
     - Quick-status badges (`CRITICAL`, `HIGH`, `MODERATE`, `LOW`).
  2. **Case Investigation Dossier (`/cases/:id`)**:
     - Victim profile and complaint details.
     - Interactive Money Trail Graph with zoom, pan, node expansion, and cycle highlight.
     - Cross-case syndicate link indicator.
     - On-demand "Generate Prediction" trigger.
  3. **Prediction & Decision Support Panel**:
     - Risk tier dial and probability gauge.
     - Prioritized Candidate ATM list with distance and cashout history.
     - Structured narrative text, risk factors, and protective factors.
  4. **Investigator Action Drawer**:
     - Fast action submission (`Freeze Account`, `Dispatch Field Alert`, `Add Note`).
     - Immutable audit history timeline.

---

### Stage 5: Interactive GIS Map & Spatial Intelligence (COMPLETE)
- **Objective**: Provide geographical situational awareness for physical cashout interventions across 300 physical terminals in India.
- **Implemented Technology & Components**:
  - **Spatial Coordinate Projection Engine**: SVG-based auto-scaling coordinate projection mapping latitude/longitude across Indian cities with pan/zoom (0.5x to 3.0x), reset controls, and responsive tooltips (`src/frontend/src/components/gis/LocationMap.tsx`).
  - **Concentric Spatial Radius Overlays**: Multi-ring visual radius overlays ($5\text{ km}$, $10\text{ km}$, $25\text{ km}$ presets and custom radii) centered on query coordinates or mule home branches with metric distance labels and Haversine distance computations.
  - **Spatial Cluster Risk Aggregation**: Grouping of physical terminals by `area_cluster_id`, geographic centroid computation, and terminal count breakdowns (`atm`, `branch`, `kiosk`) via `GET /api/v1/locations/clusters`.
  - **Cash-Out Hotspots & Frequency Markers**: High-activity withdrawal terminal discovery and risk tiering with strict anti-leakage isolation (`GET /api/v1/locations/hotspots`).
  - **One-Click Tactical Field Alert & Surveillance Dispatch**: Integrated investigator action drawer recording append-only audit entries (`target_entity_type="location"`).
- **Verification Status**: Fully verified. **20 / 20 Vitest frontend tests + 82 / 82 Pytest backend tests** passing with clean production build.

---

### Stage 6: End-to-End Integration, Demonstration & Hardening (PLANNED)
- **Objective**: Prepare the complete platform for SIH evaluation, jury demonstrations, and production deployment.
- **Deliverables**:
  1. **Docker Compose Orchestration**: Single-command containerized launch (`backend`, `frontend`, `database`, `nginx`).
  2. **Curated Demonstration Scenarios**:
     - Scenario A: High-Velocity Syndicate Cash-Out (Immediate critical alert).
     - Scenario B: Multi-Hop Layered Dispersion with Feedback Cycle.
     - Scenario C: Cold Complaint with Low Risk (Protective factors demonstrated).
  3. **Performance Profiling & Load Testing**: Sub-100ms API response times across graph reconstruction and prediction queries.
  4. **Final Hackathon Pitch & Documentation Package**: Executive summary, slide deck, and live demonstration video.

---

## 3. Transition Criteria & Quality Gates

To transition between stages, the following gates must be met:

```
[ Code Implementation ] ──► [ Unit & Integration Tests (100% Pass) ] ──► [ Anti-Leakage Audit ] ──► [ Stage Approval ]
```

1. **Zero Failing Tests**: Full test suite must execute cleanly with zero errors.
2. **Anti-Leakage Guarantee**: Automated verification that `prediction_ground_truth` and `is_future_ground_truth` are completely unreferenced in operational code.
3. **Synchronized Documentation**: `IMPLEMENTATION_STATUS.md` and `API_REFERENCE.md` updated prior to stage sign-off.

---

**Last Updated**: 2026-09-28  
**Documentation Version**: 2.0  
**Status**: Staged Roadmap Formally Approved
