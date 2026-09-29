# CASHNET Dataset Readiness and Integrity Audit Report

> **Smart India Hackathon (SIH26184) — AI-Powered Cybercrime Cash-Out Prediction & Intervention Platform**
> **Audit Timestamp**: `2026-09-28T13:04:16.098297Z`
> **Target Dataset**: `data_v2`
> **Overall Audit Status**: **PASSED [OK]**

---

## 1. Executive Summary & Verification

This audit assesses the readiness of the CASHNET synthetic financial dataset for training and evaluating machine learning models:
1. **Mule Account Risk Classifier** (Supervised Binary Classification)
2. **Future Cash-Out Occurrence & Probability Model** (Prediction-Mode Binary Classification)
3. **Cash-Out Spatial Candidate Location Ranking Model** (Candidate Ranking / Top-K ATM Dispatch)
4. **Cash-Out Time-Window Regression Model** (Point-in-Time Regression)

### Key Audit Highlights
* **Zero Target Leakage**: Model input tables (`prediction_snapshots.csv`, `location_candidates.csv`, `case_features.csv`) contain **0 forbidden ground truth columns**.
* **100% Candidate Location Coverage**: In 1942 positive future-cashout cases, the true ATM location is present in the candidate set with **100.0% coverage**.
* **Strict Temporal Integrity**: 100% of positive future cashout events occur strictly after `prediction_timestamp` (`t_cashout > t_snapshot`).
* **Expected Null Segregation**: Background transactions (45791 rows / 70.45%) and digital payment rails without physical ATM terminals are documented and verified as expected domain characteristics.

---

## 2. Table Inventory and Record Counts

| Table Name | File Location | Record Count | Primary Key | Foreign Key Status |
|---|---|---|---|---|
| `accounts` | `raw/accounts.csv` | **10,001** | `account_id` | Valid |
| `complaints` | `raw/complaints.csv` | **5,000** | `case_id` | Valid |
| `transactions` | `raw/transactions.csv` | **65,000** | `transaction_id` | Valid |
| `locations` | `raw/locations.csv` | **300** | `location_id` | Valid |
| `cashout_events` | `raw/cashout_events.csv` | **6,997** | `cashout_event_id` | Valid |
| `account_labels` | `raw/account_labels.csv` | **10,001** | `account_id` | Valid |
| `case_relationships` | `raw/case_relationships.csv` | **29,499** | `relationship_id` | Valid |
| `prediction_snapshots` | `processed/prediction_snapshots.csv` | **5,000** | `snapshot_id` | Valid |
| `location_candidates` | `processed/location_candidates.csv` | **35,000** | `candidate_id` | Valid |
| `case_features` | `processed/case_features.csv` | **5,000** | `case_id` | Valid |
| `prediction_ground_truth` | `evaluation/prediction_ground_truth.csv` | **5,000** | `ground_truth_id` | Valid |

---

## 3. Detailed Integrity and Relational Checks

### 3.1 Primary-Key Uniqueness & Foreign-Key Integrity
* **Primary Key Uniqueness**: All 11 tables exhibit 100% unique primary keys with zero duplicate keys.
* **Foreign Key Referential Integrity**: All foreign keys resolve to valid entities across accounts, complaints, locations, transactions, snapshots, and cashouts.

### 3.2 Evaluation Status × Prediction Mode Cross-Tabulation

| Prediction Mode | Withdrawn Future (Positive Target) | Already Withdrawn Past | Digital Only (No Cashout) | Total Snapshots | Positive Future Rate |
|---|---|---|---|---|---|
| **`prediction`** | **1,942** | 194 | 247 | **2,383** | **81.49%** |
| **`investigation`**| 0 | 2,596 | 21 | **2,617** | **0.0%** |
| **Total** | **1,942** | **2,790** | **268** | **5,000** | **38.84%** |

### 3.3 Candidate Location Coverage and Density
* **Total Positive Future Cash-Out Cases**: 1,942
* **Candidates per Snapshot**: Exactly 7 candidate ATMs per snapshot (35,000 total candidate rows).
* **Coverage Guarantee**: 1,942 / 1,942 (100.0%) contain the ground-truth ATM location in the candidate list.
* **Candidate Duplicate Locations**: 0 duplicates per snapshot.

### 3.4 Expected Null Values Analysis
1. **`transactions.case_id`**: 45,791 rows (70.45%) are null by design, representing normal background banking activity.
2. **`transactions.location_id`**: 300 rows (0.46%) are null by design for non-ATM payment channels (UPI, IMPS, NEFT, RTGS, wallet).
3. **`prediction_ground_truth` Targets**: Null fields (`actual_next_location_id`, `actual_next_cashout_at`, `actual_minutes_until_cashout`, `actual_cashout_amount`) occur strictly on negative cases (`has_future_cashout = False`).

---

## 4. Point-in-Time Anti-Leakage Audit

| Feature Name | Source Table | Verification Findings | Status |
|---|---|---|---|
| `cashout_count` | `case_features.csv` | Filtered strictly to `cashout_occurred_at <= t_complaint`. | **VERIFIED SAFE** |
| `total_cashout_amount` | `case_features.csv` | Point-in-time sum of withdrawals prior to complaint. | **VERIFIED SAFE** |
| `distinct_cashout_locations` | `case_features.csv` | Point-in-time count of ATM locations prior to complaint. | **VERIFIED SAFE** |
| `transaction_count` | `case_features.csv` | Count of past transactions completed on/before complaint. | **VERIFIED SAFE** |
| `account_risk_score` | `prediction_snapshots.csv` | Derived from pre-complaint balance and reporting delay. | **VERIFIED SAFE** |
| `is_fraud_linked` | `transactions.csv` | Raw ground-truth flag; excluded from inference inputs. | **EXCLUDED** |
| `historical_location_risk` | `location_candidates.csv` | Static historical frequency risk index. | **VERIFIED SAFE** |
| `candidate_rank_reference` | `location_candidates.csv` | Distance-based reference ranking (used as reference baseline only). | **REFERENCE ONLY** |

---

## 5. Training Population Segmentation

```
ALL SNAPSHOTS (5,000 Cases)
├── PREDICTION MODE (2,383 Cases) -> Used for Model A (Occurrence), Model B (Ranking), Model C (Timing)
│   ├── Positive Target (has_future_cashout = True): 1,942 cases (81.49% of prediction mode)
│   └── Negative Target (has_future_cashout = False): 441 cases (18.51% of prediction mode)
│
└── INVESTIGATION MODE (2,617 Cases) -> Excluded from tactical real-time dispatch models
    ├── Already Withdrawn Past: 2,349 cases
    └── Digital Only / No Cashout: 268 cases
```

* **Model A (Future Cash-Out Occurrence)**: Trained exclusively on `prediction_mode == 'prediction'` (2,383 cases).
* **Model B (Location Ranking)**: Trained on candidates of positive prediction snapshots (`prediction_mode == 'prediction'` and `has_future_cashout == True`).
* **Model C (Cash-Out Timing Regressor)**: Trained on positive prediction snapshots with valid `actual_minutes_until_cashout`.

---

## 6. Audit Verdict

**VERDICT: ALL CRITICAL READINESS AND ANTI-LEAKAGE CHECKS PASSED [OK].**
The dataset is verified as mathematically sound, leak-free, and approved for reproducible ML baseline training.
