# CASHNET Local Development & Engineering Guide

> **Smart India Hackathon (SIH26184)**  
> **AI-Powered Cybercrime Cash-Out Prediction & Investigator Decision-Support Platform**  
> **Documentation Version**: 2.0  
> **Last Verified**: 2026-09-28

---

## 1. Environment Setup & Prerequisites

### Prerequisites
- **Python**: `3.11+` (Verified with Python `3.11.11`)
- **Node.js**: `18+` (with `npm 9+`)
- **Package Managers**: `pip`, `npm`
- **Operating System**: Linux / macOS / Windows WSL2

### Initial Setup Commands

#### Backend Setup
```bash
# 1. Clone or navigate to the repository root
cd /home/Jarvis/Downloads/Dataset

# 2. (Optional) Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt
```

#### Frontend Setup
```bash
# 1. Navigate to the frontend directory
cd src/frontend

# 2. Install dependencies
npm install

# 3. Return to project root
cd ../..
```

---

## 2. Database Management & Migrations

CASHNET uses SQLAlchemy 2.0 ORM with Alembic migrations.

### Configuration (`src/backend/config.py`)
By default, the application connects to a local SQLite database at `cashnet_dev.db`:
- `DATABASE_URL`: `sqlite:///./cashnet_dev.db` (Default)
- For PostgreSQL production: `postgresql+psycopg2://user:password@localhost:5432/cashnet`

### Running Alembic Migrations
```bash
# Apply all pending database migrations to create/update tables
python3 -m alembic upgrade head

# Check current migration revision
python3 -m alembic current

# Create a new revision (if modifying src/backend/db/models.py)
python3 -m alembic revision --autogenerate -m "add_new_feature_column"
```

---

## 3. Synthetic Data Import & Validation

The repository includes a complete synthetic dataset of 5,000 cases, 10,001 accounts, 65,000+ transactions, and 300 locations under `data_v2/`.

### Import CLI Commands
```bash
# Perform a clean wipe and full dataset import
python3 scripts/import_data.py --wipe

# Import data without wiping existing tables (skips existing records)
python3 scripts/import_data.py

# Run relational and temporal dataset integrity validation
python3 scripts/audit_dataset.py
```

---

## 4. Starting the Application

### Option A: Backend Server (FastAPI + Uvicorn)
```bash
# Start backend development server with auto-reload
python3 -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

# Start production server (multi-worker)
python3 -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Option B: Frontend Development Server (Vite)
```bash
cd src/frontend
npm run dev
# Accessible at http://localhost:5173
```

### Interactive Documentation & Diagnostics:
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc API Documentation**: `http://localhost:8000/redoc`
- **System Health & Table Counts**: `http://localhost:8000/api/v1/health`

---

## 5. Running Automated Tests

CASHNET includes 82 automated backend tests (`pytest`) and 20 automated frontend unit/component tests (`vitest`).

### Backend Test Suite (Pytest)
```bash
# Run the full backend automated test suite (82 tests)
pytest -v

# Run specific test modules
pytest tests/test_backend_api.py -v
pytest tests/test_money_trail.py -v
pytest tests/test_network_intelligence.py -v
pytest tests/test_prediction_service.py -v
pytest tests/test_data_leakage.py -v
pytest tests/test_dataset_readiness.py -v
```

### Frontend Test Suite (Vitest)
```bash
# Run frontend tests from root
npm test

# Or run directly in src/frontend
cd src/frontend
npm test -- --run
```

### Frontend Production Build
```bash
npm run build
```

---

## 6. ML Model Training & Forensic Verification CLI

Operational scripts for ML training and verification are located in `scripts/`:

```bash
# 1. Train ML Baselines (Model A Occurrence Classifier & Model C Timing Regressor)
python3 scripts/train_baselines.py

# 2. Run independent forensic verification of model artifacts
python3 scripts/verify_models.py

# 3. Comprehensive dataset quality audit
python3 scripts/audit_dataset.py
```

---

## 7. Engineering Standards & Code Conventions

1. **Anti-Leakage Guarantee**: Never import or query `PredictionGroundTruth` in operational routes or services.
2. **Type Hints**: Use strict Python type annotations across all function signatures.
3. **Pydantic Validation**: All API inputs and outputs must map to explicit schemas in `src/backend/schemas/__init__.py`.
4. **Append-Only Immutability**: Never attempt to update or delete `InvestigatorAction` or `PredictionRecord` rows.

### Mandatory Attribution
When committing code changes:
```
Co-Authored-By: Claude Code <noreply@anthropic.com>
```

When creating pull requests:
```
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

---

**Last Updated**: 2026-09-28  
**Documentation Version**: 2.0  
**Status**: Development Guide Formally Verified
