# AGENTS.md — Mandatory Operating Instructions for All AI Coding Agents

> **Every AI coding agent working on CASHNET must read this file before performing any task.**
> This repository contains strict safety, data isolation, and engineering constraints.

---

## 1. Project Identity

**CASHNET** is an AI-assisted cybercrime investigation and cash-out risk decision-support platform developed for the Smart India Hackathon (SIH26184). It assists law enforcement agencies (LEAs) in tracking money-laundering trails across multi-hop mule account networks and prioritizing high-probability physical cash withdrawal locations (ATMs, branches, CSP kiosks) to enable rapid intervention before funds are extracted.

### Verified Technology Stack:
- **Backend**: FastAPI 0.110+, Python 3.11+
- **Database**: SQLAlchemy 2.0 ORM, Alembic migrations, SQLite (local development) / PostgreSQL-compatible
- **Data Validation & Serialization**: Pydantic v2 (Pydantic Settings)
- **Machine Learning**: scikit-learn 1.3+, joblib 1.3+, NumPy, pandas
- **Testing**: pytest 7.4+, httpx / Starlette TestClient (80 automated tests)
- **Data**: Synthetic financial transaction network (5,000 cases, 10,001 accounts, 65,000+ transactions, 300 locations)

### Current Implementation Status:
- **Stage 1 (Backend Foundation)**: Complete (FastAPI app, ORM models, Alembic migrations, CSV importer, CRUD endpoints, anti-leakage guards, append-only action audit)
- **Stage 2 (Money Trail & Network Intelligence)**: Complete (Multi-hop BFS traversal, hop-depth indexing, cycle detection, graph visualization payloads, cross-case syndicate analysis)
- **Stage 3 (ML Prediction Service Integration)**: Complete (Model A 26-feature occurrence classifier, Model B distance-based candidate ranking fallback, Model C timing baseline, structured narrative explanations, immutable `PredictionRecord` persistence)
- **Current Milestone**: Stage 3.1 Prediction Audit & Transition to Stage 4 (Investigator Dashboard UI)

---

## 2. Mandatory Workflow (Before Every Coding Task)

Every agent must follow this 12-step sequence for any task:

1. **Read Core Context**:
   - `AGENTS.md` (this file)
   - `docs/CASHNET_PROJECT_CONTEXT.md`
   - `docs/IMPLEMENTATION_STATUS.md`
   - `docs/DATA_AND_ML_CONSTRAINTS.md`
2. **Inspect Repository Files**:
   - Verify actual file paths, schemas, endpoint definitions, and model paths before referencing them.
   - Do not assume previous conversation summaries or memory entries are accurate without verifying source code.
3. **Review Existing Tests and API Contracts**:
   - Check `tests/` and Pydantic schemas in `src/backend/schemas/__init__.py`.
   - Ensure you understand request/response types and status codes.
4. **Identify the Minimal Safe Change**:
   - Plan the smallest implementation change that fulfills the request.
   - Avoid unnecessary refactoring or introducing new unrequested dependencies.
5. **Preserve Existing Behavior**:
   - Maintain API contract compatibility unless breaking changes are explicitly approved.
   - Reuse existing services, utilities, and database sessions.
6. **Implement with Quality**:
   - Match existing idiom, naming conventions, and comment density.
   - Handle edge cases, null values, and error responses properly.
7. **Add or Update Tests**:
   - When modifying or adding behavior, write corresponding unit/integration tests in `tests/`.
8. **Execute Test Suite**:
   - Run relevant pytest modules (e.g., `pytest tests/test_prediction_service.py -v`).
   - Run the full test suite (`pytest -v`) when feasible.
9. **Report Actual Test Results**:
   - Never claim tests passed unless executed and output is verified. Include actual test counts and failures.
10. **Respect Point-in-Time & Anti-Leakage Constraints**:
    - Never touch `prediction_ground_truth` in operational code.
    - Never include future cash-out events in case dossiers or inference inputs.
11. **Update Documentation**:
    - If endpoints, schemas, database models, or statuses change, update the corresponding files in `docs/`.
12. **Record Limitations and Assumptions Honestly**:
    - Document unverified assumptions, experimental model caveats, or performance constraints clearly.

---

## 3. Engineering Rules

### Inspection Before Modification
- Always read existing files before editing them.
- Check database constraints and relationships in `src/backend/db/models.py`.
- Check route parameters and dependency injections in `src/backend/api/routes/`.

### Compatibility and Reusability
- Reuse existing business services (`CaseService`, `MoneyTrailService`, `NetworkService`, `LocationService`, `PredictionService`, `HealthService`).
- Do not duplicate logic between routes and services; keep business logic in `src/backend/services/`.
- Maintain Pydantic schema validation integrity.

### Model and ML Integrity
- **Do NOT silently alter model feature order**: The 26 features in `models/feature_manifest_used.json` must remain in exact order.
- **Do NOT alter classification thresholds or preprocessing** without explicit documentation and authorization.
- **Do NOT retrain models** unless explicitly requested.
- **Do NOT deploy Model B (Random Forest Ranker)**: The artifact in `models/location_baseline.joblib` is rejected due to a synthetic candidate injection artifact. The verified distance-based fallback heuristic must be used.
- **Model C is an experimental baseline**: Acknowledge that Model C has high uncertainty (MAE ~41.8 min, R² ≈ 0.0) due to uniform random delays in the synthetic generator.

### Testing and Error Reporting
- Never fabricate test execution results.
- Report stack traces and error messages faithfully.
- Keep test fixtures hermetic and deterministic.

---

## 4. Safety, Ethics, and Data Isolation Rules

### Rule 1: Synthetic Data Declaration
All records, account identifiers, victim names, transactions, timestamps, and geographic coordinates are **purely synthetic prototypes**. The system does **NOT** access, integrate with, or claim access to real bank databases, private KYC records, Aadhaar numbers, or confidential financial intelligence. Synthetic labels reflect simulated scenarios, not proof of real-world criminality.

### Rule 2: Point-in-Time Feature Availability
- Respect `as_of` and `snapshot_id` semantics strictly across all queries.
- Only data where `timestamp <= prediction_timestamp` (or `completed_at <= as_of`) may be included in feature vectors or operational query results.
- Pre-computed snapshots reflect state at `complaint_registered_at`.

### Rule 3: Ground Truth Isolation (Anti-Leakage Protocol)
**NEVER** query or join the `prediction_ground_truth` table in operational code paths:
- Forbidden fields in operational endpoints:
  - `has_future_cashout`
  - `actual_next_location_id`
  - `actual_next_cashout_at`
  - `actual_minutes_until_cashout`
  - `actual_cashout_amount`
  - `evaluation_status`
- **NEVER** include cashout events with `is_future_ground_truth = True` in case dossiers, money trails, or inference inputs.
- `prediction_ground_truth` is strictly reserved for offline training (`scripts/train_baselines.py`) and verification (`scripts/verify_models.py`).

### Rule 4: Predictions are Advisory Only
CASHNET is an investigator decision-support platform, not an autonomous enforcement agent.
The system must **never** autonomously:
- Freeze bank accounts
- Dispatch law enforcement units
- Declare criminal guilt
- Execute legal actions

All prediction outputs must include clear narrative explanations, risk/protective factors, and explicit advisory disclaimers.

---

## 5. Repository Layout Reference

```
Dataset/ (CASHNET Root)
├── AGENTS.md                       # This file (Persistent agent instructions)
├── README.md                       # Master project overview & quickstart
├── requirements.txt                # Python runtime dependencies
├── alembic.ini                     # Alembic migration configuration
├── cashnet_dev.db                  # Local development SQLite database
│
├── docs/                           # Master Documentation Suite
│   ├── CASHNET_PROJECT_CONTEXT.md  # Single source of truth for project context
│   ├── ARCHITECTURE.md             # System architecture & component flows
│   ├── IMPLEMENTATION_STATUS.md    # Stage-by-stage implementation record
│   ├── DATA_AND_ML_CONSTRAINTS.md  # Dataset rules, feature schemas & anti-leakage
│   ├── DEVELOPMENT_ROADMAP.md      # Future development milestones & acceptance criteria
│   ├── API_REFERENCE.md            # Comprehensive REST API contract & examples
│   ├── DATABASE_SCHEMA.md          # Relational models, constraints, and ER diagram
│   └── DEVELOPMENT_GUIDE.md        # Local setup, migrations, data import, and CLI guide
│
├── src/
│   ├── backend/                    # FastAPI Backend Application
│   │   ├── main.py                 # Application factory & lifespan manager
│   │   ├── config.py               # Pydantic Settings & environment variables
│   │   ├── api/                    # API routing layer
│   │   │   ├── router.py           # API router aggregator (/api/v1)
│   │   │   └── routes/             # Endpoint handlers (health, cases, accounts, locations, predictions)
│   │   ├── db/                     # Database layer (SQLAlchemy 2.0)
│   │   │   ├── base.py             # DeclarativeBase & constraint naming
│   │   │   ├── session.py          # Engine & SessionLocal factory
│   │   │   └── models.py           # 13 ORM entities with relationships & listeners
│   │   ├── schemas/                # Pydantic v2 validation models
│   │   │   └── __init__.py         # Request/response schemas, DTOs, pagination
│   │   ├── services/               # Business logic layer
│   │   │   ├── case_service.py     # Case dossiers, filtering, search
│   │   │   ├── location_service.py # GIS coordinates & Haversine radius queries
│   │   │   ├── money_trail_service.py # Multi-hop BFS graph reconstruction & cycle detection
│   │   │   ├── network_service.py  # Cross-case syndicate intelligence & shared accounts
│   │   │   ├── prediction_service.py  # ML inference orchestration, feature assembly, provenance
│   │   │   └── health_service.py   # Diagnostic evaluator & DB monitoring
│   │   └── importer/               # Data ingestion
│   │       └── data_importer.py    # Idempotent CSV batch ingestion & integrity checker
│   │
│   └── synthetic_data/             # Synthetic Data Generation Package
│       ├── generate.py             # CLI generation orchestrator
│       ├── validate.py             # Relational & temporal validator
│       ├── export.py               # CSV export utility
│       └── generators/             # Specialized generator modules
│
├── alembic/                        # Alembic Database Migrations
│   ├── env.py                      # Migration environment
│   └── versions/
│       └── 28be09f3db97_initial_schema.py # Initial core database schema
│
├── models/                         # Serialized ML Artifacts & Manifests
│   ├── occurrence_baseline.joblib  # Model A: Occurrence Classifier (Approved Active)
│   ├── timing_baseline.joblib      # Model C: Timing Regressor (Experimental Baseline)
│   ├── location_baseline.joblib    # Model B: Candidate Ranker (REJECTED ARTIFACT — DO NOT USE)
│   ├── feature_manifest_used.json  # Strict 26-feature ordering manifest
│   └── evaluation_config.json      # Dataset split configuration & seed parameters
│
├── data_v2/                        # Synthetic Datasets (CSV)
│   ├── raw/                        # 7 raw relational tables (accounts, complaints, txs, locations, etc.)
│   ├── processed/                  # 3 processed feature tables (snapshots, candidates, case_features)
│   ├── evaluation/                 # 1 isolated ground truth table (prediction_ground_truth.csv)
│   └── manifests/                  # Quality report, dataset manifest, feature manifest
│
├── tests/                          # Automated Pytest Suite (80 tests)
│   ├── test_backend_api.py         # REST API endpoints, filtering, pagination, anti-leakage
│   ├── test_money_trail.py         # Multi-hop BFS, branching, cycles, duplicate edges
│   ├── test_network_intelligence.py# Cross-case shared accounts, syndicates, account network
│   ├── test_prediction_service.py  # Model inference, feature assembly, provenance, audit persistence
│   ├── test_data_leakage.py        # Strict ground-truth isolation invariants
│   ├── test_dataset_readiness.py   # Dataset integrity, foreign keys, temporal ordering
│   └── ...                         # Generation, reproducibility, profiles, scenarios
│
├── scripts/                        # Operational & Verification CLI Scripts
│   ├── import_data.py              # Synthetic data ingestion CLI
│   ├── train_baselines.py          # ML baseline training pipeline
│   ├── verify_models.py            # Independent forensic model verification
│   └── audit_dataset.py            # Comprehensive dataset audit
│
├── database/                       # Static SQL Schema Definitions
│   ├── schema.sql                  # PostgreSQL-compatible schema
│   ├── indexes.sql                 # Performance indexes
│   └── seed.sql                    # Seed data
│
└── reports/                        # Model & Dataset Verification Reports
    ├── model_verification_report.md# Complete ML model audit report
    ├── dataset_readiness_report.md # Dataset integrity and anti-leakage audit report
    └── ...
```

---

## 6. Key Development Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run database migrations
python3 -m alembic upgrade head

# 3. Import synthetic dataset (full wipe and reload)
python3 scripts/import_data.py --wipe

# 4. Start backend server
python3 -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Run full automated test suite
pytest -v

# 6. Run specific test module
pytest tests/test_prediction_service.py -v
```

---

## 7. Mandatory Attribution

When committing code changes:
```
Co-Authored-By: Claude Code <noreply@anthropic.com>
```

When creating pull requests, end descriptions with:
```
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

---

**Last Updated**: 2026-09-28  
**Documentation Version**: 2.0  
**Project Status**: Stage 3 Complete, Stage 4 Pending
