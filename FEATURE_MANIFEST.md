# CASHNET Feature Classification Manifest & Target Isolation Guide

> **SIH26184 — AI-Powered Cybercrime Cash-Out Prediction & Intervention Platform**

---

## 1. Overview and Anti-Leakage Architecture

In tactical cybercrime intervention (NCRP / 1930 incident response), machine learning models operate under strict temporal and information boundaries. When a cybercrime complaint is registered at `complaint_registered_at`, investigator systems must reconstruct the financial network and infer future cashout risks **using only information that existed at or before that exact point in time**.

```
[ Fraud Occurred ] ---------> [ Complaint Registered ] ---------> [ Future Cashout ]
     (t_fraud)                  (prediction_timestamp)                 (t_cashout)
         |                                |                                 |
         +------- Available Input --------+-------- Strictly Hidden --------+
```

---

## 2. Table and Column Classification

### 2.1 Model Input Tables (Allowed at Inference / Training Input)

| Table | File Path | Usage in CASHNET ML Pipeline |
|---|---|---|
| `prediction_snapshots` | `data_v2/processed/prediction_snapshots.csv` | Primary input vector for **Cash-Out Probability** and **Cash-Out Time Window** models. |
| `location_candidates` | `data_v2/processed/location_candidates.csv` | Input pairs for **Spatial Location Candidate Ranking & ATM Dispatch** model. |
| `case_features` | `data_v2/processed/case_features.csv` | Case-level topological vectors for **Forensic Syndicate & Modus Operandi Clustering**. |
| `accounts` | `data_v2/raw/accounts.csv` | Static account metadata and historical baseline volume indicators. |
| `locations` | `data_v2/raw/locations.csv` | ATM and branch spatial coordinates across Indian metropolitan clusters. |
| `transactions` | `data_v2/raw/transactions.csv` | Money trail ledger (filter `completed_at <= prediction_timestamp` at inference). |

### 2.2 Supervised Training Labels (Permitted ONLY for Model Supervision)

| Table / Target | File Path | Target Field | Applicable Model |
|---|---|---|---|
| `account_labels` | `data_v2/raw/account_labels.csv` | `is_synthetic_mule` | **Mule-Risk Classification Model** (Graph Neural Network / XGBoost) |

### 2.3 Hidden Evaluation Targets (Strictly Forbidden from Model Input)

| Table | File Path | Forbidden Evaluation Fields |
|---|---|---|
| `prediction_ground_truth` | `data_v2/evaluation/prediction_ground_truth.csv` | `has_future_cashout`, `actual_next_location_id`, `actual_next_cashout_at`, `actual_minutes_until_cashout`, `actual_cashout_amount`, `actual_next_cashout_event_id`, `evaluation_status` |

---

## 3. Sub-Task Feature Sets

### A. Mule-Risk Prediction Model
- **Target**: `account_labels.csv` -> `is_synthetic_mule` (0 or 1)
- **Features**:
  - `accounts.csv`: `account_type`, `account_age_days`, `account_status`, `baseline_transaction_count`, `baseline_monthly_inflow`, `baseline_monthly_outflow`.
  - Aggregated Transaction Metrics: Inflow/outflow velocity, fan-out degree, ratio of immediate outflows, velocity spike over baseline.
  - *Excluded*: `synthetic_profile_type`, `is_synthetic_mule`, `label_generation_reason`.

### B. Cash-Out Time Window & Probability Model
- **Target**: `prediction_ground_truth.csv` -> `has_future_cashout` (Binary), `actual_minutes_until_cashout` (Regression / Binned)
- **Features**:
  - `prediction_snapshots.csv`: `complaint_delay_minutes`, `minutes_since_last_transaction`, `incoming_transaction_count_1h`, `outgoing_transaction_count_1h`, `incoming_transaction_count_24h`, `outgoing_transaction_count_24h`, `total_inflow_24h`, `total_outflow_24h`, `estimated_remaining_amount`, `unique_incoming_sources_24h`, `linked_account_count`, `linked_case_count`, `historical_cashout_count`, `nearest_location_distance_km`, `hour_of_day`, `day_of_week`, `account_risk_score`.
  - *Excluded*: All fields in `prediction_ground_truth.csv`.

### C. Cash-Out Location Candidate Ranking Model
- **Target**: `prediction_ground_truth.csv` -> `actual_next_location_id`
- **Features**:
  - `location_candidates.csv`: `distance_from_account_km`, `historical_cashout_count`, `historical_case_count`, `historical_location_risk`.
  - Candidate-Snapshot Cross Features: Difference between account zone and ATM zone, candidate distance relative to snapshot mean distance.
  - *Candidate Coverage*: 100% of positive future cashout cases contain the ground-truth ATM location within the candidate set.

---

## 4. Automated Anti-Leakage Verification

The repository includes automated validation rules (`src/synthetic_data/validation/leakage_validation.py`) executed on every generation run. It verifies that none of the following forbidden column names appear in processed model input tables:
- `is_synthetic_mule`
- `has_future_cashout`
- `actual_next_cashout_event_id`
- `actual_next_location_id`
- `actual_next_cashout_at`
- `actual_minutes_until_cashout`
- `actual_cashout_amount`
- `evaluation_status`
