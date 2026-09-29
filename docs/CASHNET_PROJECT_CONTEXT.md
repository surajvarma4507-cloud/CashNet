# CASHNET Project Context — Master Single Source of Truth

> **Smart India Hackathon (SIH26184)**  
> **AI-Powered Cybercrime Cash-Out Prediction & Investigator Decision-Support Platform**  
> **Documentation Version**: 2.0  
> **Last Verified**: 2026-09-28

---

## 1. Project Purpose & SIH Context

**CASHNET** is an AI-assisted cybercrime investigation and cash-out risk decision-support platform engineered for the Smart India Hackathon (SIH26184).

Its primary mission is to empower law enforcement agencies (LEAs), cybercrime police stations, and financial crime investigators responding to complaints registered via the **National Cybercrime Reporting Portal (NCRP / 1930 incident response)**.

The platform provides:
1. Automated reconstruction of complex, multi-hop money laundering trails through intermediary mule networks.
2. Cross-case network intelligence to detect shared banking infrastructure and criminal syndicates.
3. Point-in-time machine learning predictions of future physical cash withdrawal likelihood and candidate ATM/branch terminal locations.
4. Explainable, evidence-backed decision support narratives to assist investigators in issuing timely account freeze orders and tactical surveillance advisories.

---

## 2. Problem Being Addressed

In India, modern financial cybercrime (e.g., UPI impersonation, digital arrest scams, fraudulent investment platforms, phishing, and remote access scams) operates with extreme velocity:

1. **Layering Velocity**: Once a victim is defrauded, funds do not remain in the primary beneficiary account. Perpetrators immediately route funds through multiple layers (Layer 1, Layer 2, Layer 3) of digital wallets and mule bank accounts within minutes.
2. **Rapid Cash Extraction**: The terminal goal of cybercrime syndicates is rapid conversion of digital money into untraceable physical currency at ATMs, branch counters, or Customer Service Point (CSP) kiosks.
3. **Investigative Lag**: Traditional inter-bank communication, manual statement reconciliation, and formal legal notices require hours or days. By the time investigators trace the chain of accounts, cash-outs have already occurred.
4. **Siloed Complaint Handling**: Complaints registered by different victims in different jurisdictions often share the same underlying mule infrastructure, but investigators lack unified cross-case intelligence to identify common syndicate hubs.

**CASHNET directly addresses these bottlenecks** by combining relational transaction ledgers, graph topology algorithms, and predictive machine learning into a single decision-support engine.

---

## 3. Intended Users & Personas

- **Cybercrime Police Officers & IOs (Investigating Officers)**: Triage incoming 1930/NCRP complaints, inspect reconstructed transaction graphs, and make swift decisions on dispatching tactical alerts or issuing emergency debit freezes.
- **State Cyber Command & Financial Intelligence Analysts**: Analyze cross-case syndicate networks, identify persistent mule accounts, and map geographic cash-out hot-spots.
- **Bank Nodal Officers & Compliance Teams**: Coordinate with LEAs to execute point-in-time account freezes and retrieve CCTV footage from flagged ATM terminals.

---

## 4. Main User Workflow

The end-to-end operational workflow in CASHNET follows a human-in-the-loop, evidence-backed lifecycle:

```mermaid
flowchart TD
    A[1. Incident Reported\nNCRP / 1930 Portal] --> B[2. Case Registration\nComplaint Ingested with Victim Profile]
    B --> C[3. Money-Trail Reconstruction\nMulti-Hop BFS Traversal & Anomaly Detection]
    C --> D[4. Cross-Case Network Analysis\nShared Mule Syndicate Discovery]
    D --> E[5. Point-in-Time Feature Assembly\nStrict Temporal Cutoff at t_complaint]
    E --> F[6. ML Inference Execution\nModel A: Occurrence | Model B: Distance Ranking | Model C: Timing]
    F --> G[7. Evidence Synthesis & Explanation\nRisk Factors, Protective Factors, Advisory Actions]
    G --> H[8. Human Investigator Review\nDecision to Freeze Account or Dispatch Alert]
    H --> I[9. Action Persistence\nAppend-Only Audit Log in DB]
```

### Detailed Operational Steps:
1. **Complaint Ingestion**: The case is indexed with victim account metadata, payment channel (UPI, IMPS, NEFT), fraud timestamp ($t_{\text{fraud}}$), and registration timestamp ($t_{\text{complaint}}$).
2. **Money-Trail Reconstruction**: The system traverses transactions initiated from the victim account, calculating hop depths, detecting feedback cycles, and flagging disconnected links.
3. **Cross-Case Intelligence**: The platform checks whether participating mule accounts have appeared in other registered complaints, computing shared transaction volumes and syndicate clusters.
4. **Point-in-Time Prediction**: On investigator request, the ML engine extracts a 26-feature vector strictly as of the complaint timestamp ($t \le t_{\text{complaint}}$).
5. **Decision Support & Narrative Generation**: The system evaluates occurrence probability (Model A), ranks candidate ATMs by spatial proximity (Model B), estimates the tactical time-window (Model C), and generates an objective narrative summary.
6. **Investigator Action & Audit**: The investigator evaluates the advisory and records an action (e.g., `account_freeze`, `dispatch_alert`, `note_added`), permanently logged in the append-only audit trail.

---

## 5. System Capabilities

### Implemented Functionality (Stages 1–3):

#### **A. Backend Foundation & Core APIs (Stage 1)**
- High-performance FastAPI backend with automatic OpenAPI schema generation.
- SQLAlchemy 2.0 ORM with 13 entity models supporting PostgreSQL and SQLite.
- Alembic database migrations managing relational schema versions.
- Batch CSV synthetic data importer with topological foreign key ordering.
- Multi-parameter case search, status filtering, amount filtering, and sorting.
- Temporal point-in-time query support across all core endpoints (`as_of` and `snapshot_id` parameters).
- Strict ground-truth isolation architecture preventing evaluation target leakage.
- Append-only investigator action audit logging protected by SQLAlchemy database event listeners.
- System diagnostic and table count monitoring (`/health` and `/api/v1/health`).

#### **B. Money-Trail Reconstruction & Graph Topology (Stage 2)**
- Multi-hop Breadth-First Search (BFS) graph traversal tracking fund movement from victim accounts.
- Deterministic hop-depth indexing ($0$ for victim, $1$ for primary layer, $2$ for secondary layer, etc.).
- Graph anomaly detection: directed feedback cycles (DFS 3-color algorithm), disconnected/unreachable links, and parallel multi-transfers.
- Automated role assignment based on observed transaction topology (`victim`, `mule_hop_1`, `mule_hop_2`, `cashout_node`).
- Graph visualization payloads formatted for frontend renderers with node degrees and graph density metrics.

#### **C. Cross-Case Network Intelligence (Stage 2)**
- Inter-case co-occurrence graph discovery linking shared intermediary and cash-out accounts.
- Syndicate cluster metrics, total syndicate volume calculations, and hub account identification.
- Account-level network intelligence profiling historical case participation, total observed inflows/outflows, and co-occurring counterparts.
- Temporal filtering on network metrics to prevent future connection leakage.

#### **D. ML Prediction Service & Decision Support (Stage 3)**
- Point-in-time feature vector assembly adhering strictly to the 26-feature schema in `models/feature_manifest_used.json`.
- **Model A (Occurrence Classifier)**: Random Forest binary classifier predicting future cashout likelihood with calibrated probabilities and risk tiering (Low, Moderate, High, Critical).
- **Model B (Candidate Location Ranking)**: Verified distance-based fallback heuristic ranking physical ATM terminals by geographical proximity (Random Forest ranker intentionally rejected due to synthetic candidate injection artifacts).
- **Model C (Timing Regressor)**: Experimental baseline estimating operational minutes until cashout with explicit high-uncertainty disclosures.
- Automated narrative explanation generator synthesizing case summaries, risk factors, protective factors, and recommended LEA interventions.
- Immutable prediction execution audit records (`PredictionRecord`) storing full feature vectors and model provenance.

### Planned / Not Yet Implemented Functionality:
- **Stage 3.1**: Comprehensive Prediction Integration Audit.
- **Stage 4**: Investigator Dashboard (Frontend UI in React/TypeScript).
- **Stage 5**: Interactive GIS Map Visualization with ATM clustering and heatmaps.
- **Stage 6**: End-to-end integration and demonstration suite.
- Live banking core integrations (1930 / I4C automated API gateways).
- Role-based access control (RBAC) and investigator authentication.

---

## 6. Technology Stack (Verified from Repository)

| Layer / Subsystem | Technology | Verified Version | Purpose in CASHNET |
|---|---|---|---|
| **Backend Framework** | FastAPI | `0.110.0+` | High-performance ASGI REST API framework |
| **Language Runtime** | Python | `3.11+` | Primary programming language |
| **Database ORM** | SQLAlchemy | `2.0.28+` | Declarative relational ORM with type annotations |
| **Database Migrations** | Alembic | `1.13.0+` | Database schema version control & migrations |
| **Data Validation** | Pydantic / Pydantic Settings | `2.6.0+` | Request parsing, response serialization, environment configs |
| **Machine Learning** | scikit-learn | `1.3.0+` | Random Forest classifiers, regressors, and pipelines |
| **Model Serialization** | joblib | `1.3.0+` | Serialized model artifact loading and persistence |
| **Data Processing** | pandas, NumPy | `2.0.0+`, `1.24.0+` | Feature manipulation, matrix assembly, statistical audits |
| **Testing Framework** | pytest, httpx | `7.4.0+`, `0.27.0+` | Unit, integration, and API testing (80 tests) |
| **ASGI Web Server** | Uvicorn | `0.28.0+` | Production ASGI application server |
| **Database (Dev/Test)** | SQLite 3 | `3.x` | Zero-configuration local development storage |
| **Database (Production)**| PostgreSQL-compatible | `15+` | Production-grade ACID relational storage |

---

## 7. Current Repository Structure

```
Dataset/ (CASHNET Root)
├── AGENTS.md                       # Persistent instructions for AI coding agents
├── README.md                       # Project overview and quickstart guide
├── requirements.txt                # Python runtime dependencies
├── alembic.ini                     # Alembic migration configuration
├── cashnet_dev.db                  # Local development SQLite database
│
├── docs/                           # Master Documentation Suite
│   ├── CASHNET_PROJECT_CONTEXT.md  # Single source of truth for project context (this file)
│   ├── ARCHITECTURE.md             # System architecture & component flows
│   ├── IMPLEMENTATION_STATUS.md    # Stage-by-stage implementation record
│   ├── DATA_AND_ML_CONSTRAINTS.md  # Dataset rules, feature schemas & anti-leakage
│   ├── DEVELOPMENT_ROADMAP.md      # Future development milestones & acceptance criteria
│   ├── API_REFERENCE.md            # Comprehensive REST API contract & curl examples
│   ├── DATABASE_SCHEMA.md          # Relational models, constraints & ER diagram
│   └── DEVELOPMENT_GUIDE.md        # Local setup, migrations, data import & CLI guide
│
├── src/
│   ├── backend/                    # FastAPI Backend Application
│   │   ├── main.py                 # FastAPI application factory & lifespan manager
│   │   ├── config.py               # Pydantic Settings & environment variables
│   │   ├── api/                    # API routing layer
│   │   │   ├── router.py           # API router aggregator (/api/v1)
│   │   │   └── routes/             # Route handlers (health, cases, accounts, locations, predictions)
│   │   ├── db/                     # Database layer (SQLAlchemy 2.0)
│   │   │   ├── base.py             # DeclarativeBase & constraint naming conventions
│   │   │   ├── session.py          # Engine & SessionLocal factory
│   │   │   └── models.py           # 13 ORM entities with relationships & listeners
│   │   ├── schemas/                # Pydantic v2 validation models
│   │   │   └── __init__.py         # Request/response schemas, DTOs, pagination
│   │   ├── services/               # Business logic layer
│   │   │   ├── case_service.py     # Case dossiers, filtering, search, transactions
│   │   │   ├── location_service.py # GIS coordinates & Haversine radius queries
│   │   │   ├── money_trail_service.py # Multi-hop BFS graph reconstruction & cycle detection
│   │   │   ├── network_service.py  # Cross-case syndicate intelligence & shared accounts
│   │   │   ├── prediction_service.py  # ML inference orchestration, feature assembly, provenance
│   │   │   └── health_service.py   # Diagnostic evaluator & DB monitoring
│   │   └── importer/               # Data ingestion
│   │       └── data_importer.py    # Idempotent CSV batch ingestion & integrity checker
│   │
│   └── synthetic_data/             # Synthetic Data Generation Package
│       ├── generate.py             # Generation orchestrator
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

## 8. Major Backend Modules and Responsibilities

### `src/backend/api/` (API Layer)
- `router.py`: Central router prefixing domain sub-routers with `/api/v1`.
- `routes/health.py`: Health diagnostics (`GET /health`, `GET /api/v1/health`).
- `routes/cases.py`: Core case dossier, transaction ledger, account lists, money trail, visual graph, network intelligence, related cases, and investigator actions.
- `routes/accounts.py`: Account-level intelligence and multi-case money trail participation.
- `routes/locations.py`: ATM and branch terminal listing with spatial radius filtering.
- `routes/predictions.py`: ML prediction execution trigger, prediction audit history, and individual prediction retrieval.

### `src/backend/services/` (Business Logic Layer)
- `case_service.py`: Case search, dossier hydration, point-in-time timestamp resolution, and action logging.
- `money_trail_service.py`: Reconstructs multi-hop transaction graphs via BFS, detects cycles via 3-color DFS, identifies disconnected links, and computes topological metrics.
- `network_service.py`: Computes cross-case shared mule links, syndicate clusters, hub accounts, and account-level network profiles.
- `location_service.py`: Manages ATM/branch metadata and executes Haversine great-circle spatial queries.
- `prediction_service.py`: Orchestrates point-in-time 26-feature vector assembly, model loading, Model A occurrence inference, Model B distance candidate ranking, Model C timing estimation, narrative synthesis, and `PredictionRecord` audit persistence.
- `health_service.py`: Evaluates database connectivity, queries live table counts, and checks ML model subsystem readiness.

### `src/backend/db/` (Data Access Layer)
- `base.py`: Declares SQLAlchemy 2.0 `Base` with automated constraint naming conventions.
- `session.py`: Manages the database engine, connection pool, and request-scoped `SessionLocal` generator.
- `models.py`: Defines 13 SQLAlchemy models with strict foreign keys, indexes, and event listeners.

### `src/backend/importer/` (Data Ingestion)
- `data_importer.py`: Provides idempotent, batch-inserted CSV ingestion with foreign key topological ordering and integrity checks.

---

## 9. Database Overview

The relational database schema is structured into four functional zones:

1. **Core Relational Evidence**:
   - `Location` (300 records): Physical ATM, branch, and CSP kiosk terminal coordinates across Indian cities.
   - `Account` (10,001 records): Synthetic savings, current, and digital wallet accounts with baseline transaction metrics.
   - `Complaint` (5,000 records): Cybercrime complaints with fraud amount, payment channel, incident timestamp, and registration timestamp.
   - `Transaction` (65,000+ records): Money trail ledger with transfer timestamps and payment channels (UPI, IMPS, NEFT, RTGS, ATM).
   - `CashoutEvent` (6,997 records): Physical cash withdrawal milestones linking accounts, locations, and transactions.
   - `AccountLabel` (10,001 records): Supervised behavioral labels (`is_synthetic_mule`) and generation rationales.
2. **Feature Engineering & Graph Topology**:
   - `PredictionSnapshot` (5,000 records): Point-in-time 26-feature vectors captured at complaint registration.
   - `LocationCandidate` (35,000 records): Spatial candidate ranking pairs (7 candidate ATMs per case).
   - `CaseFeature` (5,000 records): Forensic graph metrics (network depth, branching factor, average transaction amounts).
   - `CaseRelationship` (29,499 records): Inter-case co-occurrence links between shared mule accounts.
3. **Audit & Provenance (Immutable)**:
   - `InvestigatorAction`: Append-only audit log recording freeze orders, alerts, and investigator notes (protected against UPDATE/DELETE by SQLAlchemy event listeners).
   - `PredictionRecord`: Immutable audit records of executed prediction runs, containing complete input features, model outputs, and narrative explanations in JSON format.
4. **Isolated Evaluation Ground Truth**:
   - `PredictionGroundTruth` (5,000 records): **STRICTLY ISOLATED** table containing hidden future cashout targets (`has_future_cashout`, `actual_next_location_id`, `actual_next_cashout_at`, `actual_minutes_until_cashout`). Never queried by operational APIs.

---

## 10. API Overview

The REST API exposes 17 versioned endpoints under `/api/v1` and 1 root health check:

- **System Diagnostics**:
  - `GET /health` / `GET /api/v1/health`
- **Case Dossiers & Money Trails**:
  - `GET /api/v1/cases` (Filterable, paginated case listing)
  - `GET /api/v1/cases/{case_id}` (Complete case dossier with `as_of` / `snapshot_id` support)
  - `GET /api/v1/cases/{case_id}/transactions` (Chronological money trail ledger)
  - `GET /api/v1/cases/{case_id}/accounts` (Participating accounts with assigned roles)
  - `GET /api/v1/cases/{case_id}/money-trail` (Multi-hop reconstructed money trail with anomaly analysis)
  - `GET /api/v1/cases/{case_id}/graph` (Visual graph payload with topological metrics)
  - `GET /api/v1/cases/{case_id}/network` (Cross-case syndicate intelligence)
  - `GET /api/v1/cases/{case_id}/related-cases` (Paginated list of linked cases sharing infrastructure)
  - `POST /api/v1/cases/{case_id}/actions` (Record investigator decision in append-only log)
- **Account Intelligence**:
  - `GET /api/v1/accounts/{account_id}/network` (Multi-case account profile & co-occurring accounts)
  - `GET /api/v1/accounts/{account_id}/money-trails` (Account participation across case money trails)
- **GIS & Terminals**:
  - `GET /api/v1/locations` (ATM/branch listing with Haversine spatial radius filtering)
  - `GET /api/v1/locations/{location_id}` (Terminal coordinates and metadata)
- **ML Predictions & Decision Support**:
  - `POST /api/v1/cases/{case_id}/predictions` (Execute point-in-time ML prediction & narrative)
  - `GET /api/v1/cases/{case_id}/predictions` (Paginated prediction execution history for a case)
  - `GET /api/v1/predictions/{prediction_id}` (Retrieve immutable prediction audit record)

---

## 11. ML Subsystem Overview

```
Point-in-Time 26-Feature Vector
              │
    ┌─────────┼─────────┐
    ↓         ↓         ↓
 [Model A] [Model B] [Model C]
Occurrence Location   Timing
Classifier  Ranker   Regressor
    │         │         │
    └─────────┼─────────┘
              ↓
Decision Support Narrative + PredictionRecord
```

### Model A: Future Cash-Out Occurrence Classifier
- **Model Type**: Binary Classification (scikit-learn `RandomForestClassifier` within an imputer pipeline).
- **Artifact Path**: `models/occurrence_baseline.joblib`.
- **Feature Inputs**: 26 continuous and discrete point-in-time features from `models/feature_manifest_used.json`.
- **Target Variable**: `has_future_cashout` (Boolean).
- **Status**: **APPROVED ACTIVE**.
- **Verified Performance**: **86.16% Accuracy, 0.8617 ROC-AUC, 0.9569 PR-AUC, 0.1245 Brier Score, 0.0573 ECE** on independent test set.
- **Risk Tiers**: Low ($< 0.30$), Moderate ($0.30 - 0.60$), High ($0.60 - 0.85$), Critical ($\ge 0.85$).

### Model B: Candidate Location Prioritizer
- **Operational Strategy**: **Distance-Based Proximity Fallback Baseline**.
- **Algorithm**: Candidate ATMs sorted by `distance_from_account_km` ascending, with tie-breaking by `historical_cashout_count` descending.
- **Performance**: **71.73% Top-1 Accuracy** on test set.
- **Rejected Artifact**: `models/location_baseline.joblib` (Random Forest Spatial Ranker).
- **Rejection Reason**: The learned Random Forest exploited a synthetic dataset injection artifact where distant ATMs were artificially injected into candidate sets, creating an unrepresentative bimodal distribution ($P(\text{Target} \mid \text{dist} > 50\text{km}) = 88.74\%$). Deploying this model in the real world would fail disastrously; hence, the distance baseline is strictly enforced.

### Model C: Cash-Out Timing Estimator
- **Model Type**: Regression (scikit-learn `RandomForestRegressor` within an imputer pipeline).
- **Artifact Path**: `models/timing_baseline.joblib`.
- **Feature Inputs**: Same 26 point-in-time features as Model A.
- **Target Variable**: `actual_minutes_until_cashout` (Float).
- **Status**: **EXPERIMENTAL BASELINE (HIGH UNCERTAINTY)**.
- **Performance**: **41.83 min MAE, $R^2 \approx 0.00$**.
- **Uncertainty Justification**: In the synthetic generator, future cashout delays were generated from $\text{Uniform}(10, 180\text{ minutes})$ independently of graph features. Theoretical median error for this distribution is $(180 - 10) / 4 = 42.50\text{ min}$, matching the observed MAE. The model output is presented with an explicit high-uncertainty disclaimer.

---

## 12. Data Sources and Synthetic Data Assumptions

1. **Synthetic Generation**: All data was generated using `src/synthetic_data/` to model realistic cybercrime topologies without compromising sensitive financial data.
2. **Geographic Realism**: 300 ATM/branch terminals are distributed across 13 major Indian metropolitan clusters (Mumbai, Delhi-NCR, Bengaluru, Hyderabad, Kolkata, Chennai, Ahmedabad, Pune, Jaipur, Lucknow, Patna, Bhopal, Chandigarh) with coordinates bounded by India's geographic polygon ($6.0^\circ \text{N} - 38.0^\circ \text{N}$, $68.0^\circ \text{E} - 98.0^\circ \text{E}$).
3. **Fraud Typologies**: Synthetic complaint scenarios cover major Indian cybercrime categories: UPI fraud, investment/part-time job scams, digital arrest scams, phishing, remote access trojans, and sextortion.
4. **Payment Rails**: Transactions realistically emulate Indian domestic settlement channels: UPI (immediate), IMPS (immediate), NEFT (batch), RTGS (large-value), and ATM withdrawals.

---

## 13. Security, Privacy, and Human-Oversight Principles

1. **Strictly Synthetic / Zero PII**: The system contains no real Indian citizen Aadhaar numbers, real bank account numbers, phone numbers, or PAN records.
2. **Advisory Decision Support Only**: CASHNET outputs are tactical recommendations. Law enforcement officers retain full legal authority and responsibility for issuing freeze orders or deploying field surveillance.
3. **Immutable Audit Trails**: Every investigator action is immutably timestamped and recorded. Updates and deletions on `InvestigatorAction` are blocked at the ORM layer.
4. **Point-in-Time Anti-Leakage Protocol**: Features and graph networks only reflect evidence available prior to complaint registration, preventing operational bias or lookahead contamination.
5. **Human-Understandable Explanations**: All predictions are accompanied by structured explanations highlighting specific observed risk factors and mitigating protective factors.

---

## 14. Clear Distinction Between the Five Data Types

To prevent conceptual confusion, every agent and engineer must strictly distinguish between these five data layers:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. OBSERVED TRANSACTION EVIDENCE (Empirical / Relational)               │
│    - Past transactions completed at t <= t_complaint                    │
│    - Actual bank account ages, types, and home branch locations         │
│    - Registered complaint amounts and victim reports                    │
├─────────────────────────────────────────────────────────────────────────┤
│ 2. DERIVED GRAPH METRICS (Deterministic Graph Topologies)               │
│    - Hop-depth index (BFS distance from victim)                         │
│    - Graph branching factor, network depth, and cycle flags             │
│    - Cross-case shared account co-occurrence links                      │
├─────────────────────────────────────────────────────────────────────────┤
│ 3. MODEL PREDICTIONS (Statistical / Advisory Estimates)                 │
│    - Probability of future cashout (Model A: 0.0 to 1.0)                │
│    - Risk tier categorization (Low, Moderate, High, Critical)           │
│    - Proximity-ranked candidate ATM terminals (Model B)                 │
│    - Estimated intervention time-window (Model C)                       │
├─────────────────────────────────────────────────────────────────────────┤
│ 4. SYNTHETIC EVALUATION GROUND TRUTH (Hidden / Evaluation-Only)         │
│    - has_future_cashout, actual_next_location_id, actual_next_cashout_at│
│    - Stored strictly in prediction_ground_truth                         │
│    - NEVER accessible to operational services or public APIs            │
├─────────────────────────────────────────────────────────────────────────┤
│ 5. INVESTIGATOR DECISIONS (Human Action & Audit Log)                   │
│    - Freeze requests dispatched via 1930 / I4C gateways                 │
│    - CCTV surveillance alerts and field notes                           │
│    - Append-only records in investigator_actions                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 15. Current Implementation Status

| Stage | Milestone Description | Status | Validation Status |
|---|---|:---:|---|
| **Stage 1** | Backend Foundation, SQLAlchemy Models, Alembic Migrations, Data Importer, CRUD APIs | **COMPLETE** | 47 tests passed (historically reported) |
| **Stage 2** | Multi-Hop Money Trail Reconstruction, Graph Topology, Anomaly Detection, Cross-Case Network Intelligence | **COMPLETE** | 71 tests passed (historically reported) |
| **Stage 3** | ML Prediction Service Integration (Models A, B, C), Feature Assembly, Decision Support Narratives, Prediction Persistence | **COMPLETE** | **80 tests passed** (verified on 2026-09-28) |
| **Stage 3.1**| Prediction Integration Audit & Provenance Verification | **NEXT MILESTONE** | Planned |
| **Stage 4** | Investigator Dashboard (Frontend UI) | **PENDING** | Planned |
| **Stage 5** | GIS & Interactive Map Visualization | **PENDING** | Planned |
| **Stage 6** | End-to-End Integration, Demonstration & Deployment Hardening | **PENDING** | Planned |

---

## 16. Known Technical & Operational Limitations

1. **Model B Learned Ranker Rejection**: The learned Random Forest location ranker cannot be used due to synthetic candidate generation artifacts. The platform operates on a verified distance-based fallback heuristic.
2. **Model C Timing Variance**: Timing predictions carry high uncertainty ($R^2 \approx 0.0$, MAE ~41.8 min) due to uniform distribution generation in the synthetic dataset.
3. **No Real-Time Push Gateway**: Predictions and graph reconstructions are executed synchronously on-demand via REST queries; real-time WebSocket or Webhook dispatch is not yet implemented.
4. **Single-Node Prototype Database**: Default local deployment utilizes SQLite; production scale requires PostgreSQL with connection pooling.
5. **No Live Bank Integrations**: The system does not directly interact with live core banking systems or automated 1930/I4C freeze gateways.

---

## 17. Current Next Development Milestone

### Immediate Focus: Stage 3.1 Prediction Integration Audit
Before initiating frontend development (Stage 4), an exhaustive audit of Stage 3 should verify:
- Exact feature schema consistency across all 26 feature columns.
- Correct error handling on missing model artifacts.
- Absolute isolation of `prediction_ground_truth` across all newly created endpoints.
- Proper persistence and JSON serialization of `PredictionRecord` payloads.

Following Stage 3.1, work will transition to **Stage 4: Investigator Dashboard** (React/TypeScript user interface).

---

**Last Updated**: 2026-09-28  
**Documentation Version**: 2.0  
**Status**: Stage 3 Verified Complete
