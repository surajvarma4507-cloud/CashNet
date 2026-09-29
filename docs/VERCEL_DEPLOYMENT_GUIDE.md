# CASHNET (SIH26184) — Vercel Deployment & Operation Guide

> **Official Deployment Runbook for Deploying CASHNET on Vercel without Docker, Kubernetes, or Server Administration.**

---

## 1. Executive Summary

This guide provides the complete, deterministic procedure for deploying the **CASHNET AI-Assisted Cybercrime Cash-Out Intervention Platform** (SIH26184) to **Vercel**.

### Architecture Overview:
- **Frontend**: React 18 + Vite SPA with TypeScript and Tailwind CSS, compiled to static assets and served globally via Vercel Edge Network / CDN.
- **Backend API & ML Service**: FastAPI Python 3.11+ application hosted as a Vercel Serverless Function via `api/index.py` with full ASGI routing.
- **Database**: Externally hosted managed PostgreSQL (e.g. Neon, Supabase, Vercel Postgres, AWS RDS) with serverless connection pooling (`pool_pre_ping=True`, `pool_recycle=300`).
- **ML Inference**: Pre-trained scikit-learn model artifacts (Model A occurrence classifier, Model B distance-based spatial candidate ranker, Model C timing baseline) running within Vercel's standard 1024MB serverless memory limits with zero runtime model training.

---

## 2. Files Created & Modified for Vercel Deployment

| File | Purpose |
|------|---------|
| `vercel.json` | Vercel deployment configuration: builds Vite frontend, sets serverless function memory/timeout, and maps `/api/*`, `/health`, `/docs`, and SPA rewrites. |
| `api/index.py` | Vercel Python Serverless Function entry point exporting the FastAPI ASGI `app` instance. |
| `package.json` | Root workspace configuration orchestrating frontend build and test scripts. |
| `requirements.txt` | Python runtime dependencies including `psycopg2-binary` for PostgreSQL connectivity. |
| `src/backend/config.py` | Environment configuration with automated `postgres://` -> `postgresql://` normalization and resilient CORS parsing. |
| `src/backend/db/session.py` | SQLAlchemy engine with serverless connection pooling and recycling. |
| `src/backend/services/prediction_service.py` | Model directory resolver searching local, relative, and `/var/task` paths. |
| `src/backend/main.py` | Safe schema table initialization preventing DDL crashes on serverless startup. |
| `src/frontend/src/api/client.ts` | Configurable API client supporting `VITE_API_BASE_URL` with automatic same-origin fallback. |
| `src/frontend/src/vite-env.d.ts` | TypeScript definitions for Vite environment variables. |
| `src/frontend/vite.config.ts` | Vite production build output configuration (`dist`). |
| `.env.example` | Production and local environment variable documentation. |

---

## 3. Database Setup & Migration (Managed PostgreSQL)

Vercel Serverless Functions have ephemeral, read-only filesystems. A hosted PostgreSQL database is required for production persistence.

### Recommended Providers:
- **Neon Serverless Postgres** (Recommended — free tier, native branching, serverless connection pooling): [neon.tech](https://neon.tech)
- **Supabase** (PostgreSQL with pooled connections): [supabase.com](https://supabase.com)
- **Vercel Postgres** (Powered by Neon): [vercel.com/storage/postgres](https://vercel.com/storage/postgres)
- **AWS RDS / Render PostgreSQL / Aiven**

### Step-by-Step Database Initialization:

#### 1. Obtain PostgreSQL Connection String
Create a new database instance and copy the connection string:
```
postgresql://<user>:<password>@<host>/<database>?sslmode=require
```

#### 2. Run Alembic Database Migrations
From your local environment or deployment CI runner:
```bash
export DATABASE_URL="postgresql://<user>:<password>@<host>/<database>?sslmode=require"
python3 -m alembic upgrade head
```

#### 3. Import Synthetic Dataset (Idempotent Data Ingestion)
Populate the 5,000+ synthetic cases, 10,001 accounts, 65,000+ transactions, and 300 locations:
```bash
export DATABASE_URL="postgresql://<user>:<password>@<host>/<database>?sslmode=require"
python3 scripts/import_data.py --wipe
```

#### 4. Validate Database Integrity
```bash
python3 scripts/import_data.py --validate-only
```

---

## 4. Vercel Dashboard Configuration

### Step 1: Connect GitHub Repository
1. Log into your Vercel dashboard at [vercel.com](https://vercel.com).
2. Click **Add New...** → **Project**.
3. Import your GitHub repository containing the CASHNET codebase.

### Step 2: Configure Project Settings
In the Vercel project configuration screen:

| Setting | Value |
|---------|-------|
| **Framework Preset** | **Vite** (or **Other**) |
| **Root Directory** | `./` (Leave as repository root) |
| **Build Command** | `npm run build` (or `cd src/frontend && npm install && npm run build`) |
| **Output Directory** | `src/frontend/dist` |
| **Install Command** | `npm install` |

### Step 3: Configure Environment Variables
In the **Environment Variables** section, add the following:

| Variable Name | Required | Example / Value | Description |
|---------------|----------|-----------------|-------------|
| `DATABASE_URL` | **Yes** | `postgresql://user:pass@ep-sample.neon.tech/neondb?sslmode=require` | Hosted PostgreSQL connection string. |
| `CORS_ORIGINS` | Optional | `["*"]` or `https://your-domain.vercel.app` | Allowed CORS origins (JSON array or comma-separated). |
| `SIMULATION_MODE` | Optional | `true` | Declares all records and predictions are synthetic prototypes. |
| `DEBUG` | Optional | `false` | Disable debug tracebacks in production. |
| `MODELS_DIR` | Optional | `models` | Directory containing joblib ML artifacts. |
| `DEFAULT_DATA_DIR` | Optional | `data_v2` | Synthetic dataset directory. |
| `VITE_API_BASE_URL` | Optional | *(Leave empty for same-origin routing)* | Custom API base URL if deploying frontend separately. |

### Step 4: Deploy
Click **Deploy**. Vercel will:
1. Build the React + Vite frontend into `src/frontend/dist`.
2. Discover `api/index.py` and package the FastAPI Python Serverless Function with `requirements.txt`.
3. Apply rewrites defined in `vercel.json`.

---

## 5. Mule Trail & Network Intelligence Verification

CASHNET includes a multi-hop money trail reconstruction engine:
- **BFS Hop-Depth Indexing**: Traces transaction hops starting from the victim account (`hop_level: 0`).
- **Structural Anomaly Detection**:
  - Directed cycles (3-color DFS state machine).
  - Missing links / island accounts.
  - Branching factor computation.
  - Duplicate transaction deduplication.
- **Strict Anti-Leakage Protocol**: Excludes all future ground-truth cashouts (`is_future_ground_truth = True`) from money trail graphs and investigator dossiers.

### Verify Mule Trail Locally or against Live Deployment:
```bash
# Test specific case money trail via curl
curl -s "https://your-app.vercel.app/api/v1/cases/CASE_2026_000750/money-trail" | jq .
```

Expected response payload:
```json
{
  "case_id": "CASE_2026_000750",
  "victim_account_id": "ACC_IND_008682",
  "nodes": [
    {
      "account_id": "ACC_IND_008682",
      "role": "source_account",
      "hop_level": 0,
      "in_degree": 0,
      "out_degree": 1
    },
    {
      "account_id": "ACC_IND_008683",
      "role": "intermediary",
      "hop_level": 1,
      "in_degree": 1,
      "out_degree": 1
    }
  ],
  "ledger": [
    {
      "transaction_id": "TX_2026_002891",
      "from_account_id": "ACC_IND_008682",
      "to_account_id": "ACC_IND_008683",
      "amount": 45095.76,
      "hop_index": 1
    }
  ],
  "anomalies": {
    "has_cycles": false,
    "has_branching": false,
    "total_hops": 2,
    "max_depth": 2
  }
}
```

---

## 6. Live Verification Checklist

Once deployed to Vercel, verify the following endpoints using your browser or `curl`:

1. **Frontend Dashboard**:
   - Open `https://<your-project>.vercel.app/`
   - Verify that the CASHNET header, navigation tabs (Dashboard, Cases, Accounts, Locations GIS), and status indicator appear.

2. **Backend Health Check**:
   - Request `https://<your-project>.vercel.app/health`
   - Expected status: `{"status": "healthy", "database_connected": true, "version": "2.0.0"}`

3. **Case Dossiers**:
   - Request `https://<your-project>.vercel.app/api/v1/cases?page=1&page_size=10`
   - Verify pagination and case summaries.

4. **Money Trail Graph**:
   - Navigate to any case in the UI and click the **Money Trail** tab.
   - Verify that the interactive SVG graph renders accounts, hops, and chronological ledger.

5. **ML Prediction Decision Support**:
   - Click **Trigger Risk Prediction** on a case dossier.
   - Verify that the occurrence probability, risk tier, ranked candidate locations, and advisory explanation are returned.

6. **Interactive API Documentation**:
   - Open `https://<your-project>.vercel.app/docs` (Swagger UI) or `/redoc`.

---

## 7. Operational Safeguards & Constraints

1. **Synthetic Data Only**:
   All entities, accounts, names, and transaction trails are synthetic prototypes generated for SIH26184 evaluation. No real KYC, banking, or PII is used.
2. **Advisory Decision Support**:
   CASHNET outputs are advisory risk assessments designed for law enforcement analysts. The system does not execute automated banking freezes, police dispatches, or legal declarations.
3. **Point-in-Time Integrity**:
   All ML inference and dossier reconstructions respect `as_of` temporal filters, preventing data leakage across incident timelines.
