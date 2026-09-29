# CASHNET ML Baseline Models — Independent Verification & Audit Report

> **Smart India Hackathon (SIH26184) — AI-Powered Cybercrime Cash-Out Prediction & Intervention Platform**
> **Audit Date**: `2026-09-28T13:16:29.140946Z`
> **Verification Seed**: `42`
> **Target Dataset**: `data_v2`

---

## 1. Executive Summary & Readiness Verdict

An independent forensic audit was conducted on all three baseline ML models, serialized pipelines in `models/`, evaluation scripts, and dataset tables in `data_v2/`.

### Model Integration Status Summary

| Model | Task | Test Performance | Verification Finding | Integration Status |
|---|---|---|---|:---:|
| **Model A: Future Cash-Out Occurrence** | Binary Classification (`has_future_cashout`) | **86.16% Acc, 0.8617 ROC-AUC, 0.9569 PR-AUC** | All features verified strictly at point-in-time t <= t_complaint. Good calibration (Brier 0.1245, ECE 0.0573). | **SAFE TO PROCEED [READY]** |
| **Model B: Location Candidate Ranker** | Spatial Candidate Ranking (`actual_next_location_id`) | **95.81% Top-1 (RF)** vs **71.73% (Distance)** | **Synthetic candidate selection artifact detected**: Non-linear RF exploits forced distant candidate injections (P(target | dist > 50km) = 88.7%). | **REQUIRES FIX [NOT READY]** |
| **Model C: Cash-Out Timing Regressor** | Point-in-Time Regression (`actual_minutes_until_cashout`) | **41.83 min MAE, R^2 = 0.0000** | Mathematically exact target (t_cashout - t_snapshot). R^2 ~ 0 is caused by uniform random delay Uniform(10, 180) in generator. | **BENCHMARK ONLY [CAUTION]** |

---

## 2. Location Ranker Leakage & Selection Artifact Review (Model B)

### 2.1 Feature Columns & Timestamp Audit
* **Input Features**: `['distance_from_account_km', 'historical_cashout_count', 'historical_case_count', 'historical_location_risk']`
* **Forbidden Fields Audit**: Explicitly verified that `actual_next_location_id`, `candidate_rank_reference`, `has_future_cashout`, `evaluation_status`, and `actual_next_cashout_event_id` are **0% present in model inputs**.
* **Split Integrity**: 100% of candidate rows for a given snapshot remain strictly grouped within the same data split (0 cross-split leakage).

### 2.2 Forensic Analysis: Why Random Forest Achieves 95.81% Top-1 vs Distance 71.73%

In `src/synthetic_data/generators/ground_truth.py`:
```python
# Candidate generation logic:
selected_cand_locs = all_sorted_locs[:num_candidates_target] # Select 7 nearest ATMs

# Enforce candidate coverage:
if future_loc_id and future_loc_id not in [l["location_id"] for l in selected_cand_locs]:
    actual_loc_obj = location_lookup.get(future_loc_id)
    if actual_loc_obj:
        selected_cand_locs[-1] = actual_loc_obj # Replace 7th candidate with distant target
```

#### The Synthetic Selection Artifact:
1. **Target ATMs**:
   * **69.67%** (1,353 cases) occur at `distance == 0.0 km` (home account location).
   * **23.53%** (457 cases) occur at `distance > 50.0 km` (distant city / cross-metro cashouts).
2. **Non-Target Candidate ATMs**:
   * **4.42%** (515 candidates) have `distance == 0.0 km`.
   * **Only 0.50%** (58 candidates) have `distance > 50.0 km`.
3. **Statistical Artifact**:
   * When a candidate has `distance_from_account_km > 50 km`, the probability that it is the ground-truth target is:
     **P(Target | Distance > 50km) = 457 / (457 + 58) = 88.74%**
   * The **Distance Baseline** ranks nearest ATMs first, correctly identifying local cashouts (71.73% Top-1) but ranking distant cashouts 7th.
   * The non-linear **Random Forest** learns a U-shaped / bimodal decision boundary: boosting candidates with dist == 0 **AND** candidates with dist > 50, artificially inflating Top-1 accuracy to 95.81%.
   * Linear Logistic Regression cannot fit this bimodal distribution, achieving only 27.75% Top-1.

**Action Required**: Do not deploy the Random Forest candidate ranker until candidate generation is upgraded to realistic geographic clustering (e.g. searching nearby terminals in the transit city rather than injecting a distant ATM into the home account's cluster).

---

## 3. Timing Target & Generator Dynamics Review (Model C)

### 3.1 Target Definition Verification
* **Target Field**: `actual_minutes_until_cashout` in `data_v2/evaluation/prediction_ground_truth.csv`.
* **Exact Timestamp Verification**: Verified against raw timestamps:
  **actual_minutes_until_cashout = (t_cashout - t_prediction_timestamp) / 60**
* **Verification Result**: **100% exact match across all 1,942 positive cases**. Zero negative values, zero missing values on positive cases.

### 3.2 Regression Baseline Performance

| Model | Test MAE | Test MedianAE | Test RMSE | Test R^2 |
|---|---|---|---|---|
| **Median Baseline** | 42.24 min | 42.00 min | 49.50 min | -0.0024 |
| **Random Forest Regressor** | 41.83 min | 41.20 min | 49.44 min | 0.0000 |

#### Explanation of R^2 ~ 0.00:
In `src/synthetic_data/generators/networks.py` line 77:
```python
mins_after_complaint = rng.randint(10, 180)
return t_complaint + timedelta(minutes=mins_after_complaint)
```
The timing delay is generated from a uniform distribution Uniform(10, 180) independently of graph features. For any continuous uniform distribution Uniform(a, b), the theoretical mean absolute error of the median predictor is:
**MAE_theoretical = (b - a) / 4 = (180 - 10) / 4 = 42.50 minutes**
The observed MAE of **41.83 minutes** matches theoretical expectation. The regression baseline is mathematically sound but limited by the synthetic generator's uncorrelated delay distribution.

---

## 4. Occurrence Classifier Verification & Calibration (Model A)

### 4.1 Feature Availability & Provenance Audit

| Feature Name | Source Table | Point-in-Time Availability | Verification Notes |
|---|---|---|---|
| `total_cashout_amount` | `case_features.csv` | strictly t <= t_complaint | Sum of cashouts occurred before complaint registration. 0 future events included. |
| `historical_cashout_count` | `prediction_snapshots.csv` | strictly t <= t_complaint | Count of past cashouts before complaint registration. |
| `account_risk_score` | `prediction_snapshots.csv` | strictly t <= t_complaint | Heuristic derived from pre-complaint balance and reporting delay. |
| `minutes_since_last_transaction` | `prediction_snapshots.csv` | strictly t <= t_complaint | Derived strictly from transactions completed before complaint. |

### 4.2 Comprehensive Evaluation & Calibration Metrics

| Metric | Test Set Value | Description |
|---|---|---|
| **Accuracy** | **86.16%** | Overall correct binary classifications |
| **Precision** | **90.93%** | Positive predictive value (true positive cashouts / predicted positive) |
| **Recall** | **91.88%** | True positive rate (caught cashouts / actual positive) |
| **F1 Score** | **0.9141** | Harmonic mean of precision and recall |
| **ROC-AUC** | **0.8617** | Area under ROC curve |
| **PR-AUC** | **0.9569** | Area under Precision-Recall curve |
| **False Positive Rate (FPR)** | **36.84%** | False alarms on negative / already withdrawn cases |
| **Brier Score** | **0.1245** | Mean squared probability error (lower is better, <= 0.15 is well-calibrated) |
| **Log Loss** | **0.3866** | Cross-entropy loss |
| **Expected Calibration Error (ECE)** | **0.0573** | Weighted difference between confidence and empirical accuracy |

#### Test Confusion Matrix
* **True Negatives (TN)**: 60 cases
* **False Positives (FP)**: 35 cases
* **False Negatives (FN)**: 31 cases
* **True Positives (TP)**: 351 cases

---

## 5. Summary & Actionable Recommendations

### 1. Integration Status
* **SAFE FOR INTEGRATION**: **Model A (Occurrence Classifier)** is fully verified, leak-free, well-calibrated, and ready for integration into the CASHNET intervention pipeline.
* **DO NOT INTEGRATE RF RANKER**: **Model B (Random Forest Ranker)** must **not** be integrated due to the candidate injection artifact. The **Distance-Only Baseline (71.73% Top-1)** should be used as the operational dispatch heuristic until candidate generation is upgraded.
* **OPERATIONAL BENCHMARK**: **Model C (Timing Regressor)** should be documented as an operational baseline with expected error bounded by the current synthetic data distribution.

### 2. Commands to Reproduce Verification & Benchmarks
```bash
# 1. Run Complete Dataset Readiness Audit
python3 scripts/audit_dataset.py --data-dir data_v2 --output-dir reports

# 2. Train All Baseline Pipelines (Seed 42)
python3 scripts/train_baselines.py --data-dir data_v2 --models-dir models --reports-dir reports --seed 42

# 3. Execute Independent Forensic Verification
python3 scripts/verify_models.py --data-dir data_v2 --models-dir models --reports-dir reports

# 4. Run Automated Test Suite
python3 -m unittest discover -s tests -v
```
