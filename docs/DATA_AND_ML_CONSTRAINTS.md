# CASHNET Data and Machine Learning Constraints

> **Smart India Hackathon (SIH26184)**  
> **AI-Powered Cybercrime Cash-Out Prediction & Investigator Decision-Support Platform**  
> **Documentation Version**: 2.0  
> **Last Verified**: 2026-09-28

---

## 1. Synthetic Data Declaration & Zero PII Guarantee

1. **Purely Synthetic Prototypes**: Every bank account number, victim profile, phone number, IFSC code, transaction identifier, complaint record, and coordinate pair in CASHNET is generated algorithmically by `src/synthetic_data/`.
2. **Zero Real-World PII**: The repository contains **NO real Indian citizen personal identifiable information (PII)**, no real Aadhaar numbers, no real PAN numbers, and no confidential financial intelligence from the Indian Cyber Crime Coordination Centre (I4C) or Reserve Bank of India (RBI).
3. **Synthetic Labels are Non-Judicial**: Synthetic mule labels (`is_synthetic_mule = True`) and risk tiers (`CRITICAL`, `HIGH`) are mathematical artifacts generated for simulation purposes and **do not constitute legal evidence or declarations of criminal guilt**.

---

## 2. Point-in-Time Feature Engineering Principles

### 2.1 Temporal Integrity Requirement ($t \le t_{\text{prediction}}$)
In cybercrime investigation, predictions must be made using **only information available to the investigating officer at the time of complaint registration**. Any use of future transaction data or post-complaint cashout events constitutes temporal leakage and invalidates forensic integrity.

```
Timeline:
────[ Fraud Event: t_fraud ]────────[ Complaint Registered: t_complaint ]───────[ Future Cash-Out: t_cashout ]────►
                                               ▲
                                               │
                                 POINT-IN-TIME AS-OF BOUNDARY
                                 (Only t <= t_complaint visible)
```

### 2.2 Point-in-Time Rules:
- **`as_of` Query Parameter**: When specified in an API request, all transaction queries must enforce `Transaction.completed_at <= as_of`.
- **Default Cutoff**: If `as_of` is omitted, the cutoff defaults to `Complaint.complaint_registered_at`.
- **`PredictionSnapshot` Table**: Pre-computed feature vectors are locked to the exact timestamp of complaint registration (`snapshot_timestamp = complaint_registered_at`).

---

## 3. Anti-Leakage Protocol & Ground Truth Isolation

### 3.1 Ground Truth Table Isolation
The table `prediction_ground_truth` is strictly designated for offline training (`scripts/train_baselines.py`) and verification (`scripts/verify_models.py`).

**Forbidden Operational Fields (NEVER query in services or routes)**:
- `has_future_cashout`
- `actual_next_location_id`
- `actual_next_cashout_at`
- `actual_minutes_until_cashout`
- `actual_cashout_amount`
- `evaluation_status`

### 3.2 Cashout Event Visibility Filtering
The `CashoutEvent` table contains both historical cashouts (completed before complaint registration) and future cashouts (used as ground truth targets).
- **Rule**: Operational code querying `CashoutEvent` must strictly filter `CashoutEvent.is_future_ground_truth == False`.
- Any cashout event where `is_future_ground_truth = True` must never be rendered in case dossiers, money trails, or graph payloads.

---

## 4. Machine Learning Subsystem & Forensic Audit

```
                              Feature Vector (26 Features)
                                           │
             ┌─────────────────────────────┼─────────────────────────────┐
             ↓                             ↓                             ↓
     [Model A: Classifier]         [Model B: Ranker]             [Model C: Regressor]
   RandomForestClassifier         Distance Fallback             RandomForestRegressor
   Approved Active (86.2%)        Verified (71.7% Top-1)        Experimental Baseline (MAE 41.8m)
```

---

### 4.1 Feature Ordering Manifest (Strict 26 Features)

Models A and C require feature vectors in the exact column order defined in `models/feature_manifest_used.json`:

| Index | Feature Name | Data Type | Description |
|:---:|---|:---:|---|
| 0 | `victim_account_age_days` | Float | Age of victim account in days |
| 1 | `amount` | Float | Total defrauded amount (INR) |
| 2 | `hop_count` | Float | Number of transaction hops observed |
| 3 | `unique_accounts_count` | Float | Total distinct accounts involved in money trail |
| 4 | `terminal_accounts_count` | Float | Leaf/endpoint accounts in the transaction graph |
| 5 | `max_hop_depth` | Float | Maximum depth reached from victim |
| 6 | `graph_branching_factor` | Float | Average out-degree of intermediate nodes |
| 7 | `initial_transfer_amount` | Float | Value of the primary first-hop transfer |
| 8 | `has_layer_1_dispersion` | Float | Binary (1.0 if funds split across multiple accounts at hop 1) |
| 9 | `layer_1_account_count` | Float | Count of primary recipient accounts |
| 10 | `layer_2_account_count` | Float | Count of secondary recipient accounts |
| 11 | `total_flow_amount` | Float | Total cumulative transaction volume |
| 12 | `flow_amount_ratio` | Float | Ratio of total flow amount to complaint amount |
| 13 | `mean_transfer_amount` | Float | Mean transaction transfer value |
| 14 | `max_transfer_amount` | Float | Maximum single transaction value |
| 15 | `min_transfer_amount` | Float | Minimum single transaction value |
| 16 | `time_to_complaint_mins` | Float | Elapsed minutes between fraud and registration |
| 17 | `known_mule_count` | Float | Count of flagged synthetic mule accounts |
| 18 | `high_risk_mule_count` | Float | Count of high-risk flagged accounts |
| 19 | `has_known_mule` | Float | Binary (1.0 if at least one mule is present) |
| 20 | `mean_account_age_days` | Float | Average age of all participating accounts |
| 21 | `min_account_age_days` | Float | Minimum account age (identifies fresh mules) |
| 22 | `rapid_transfer_flag` | Float | Binary (1.0 if transfers occurred in < 15 mins) |
| 23 | `round_amount_flag` | Float | Binary (1.0 if transactions are rounded figures) |
| 24 | `prior_case_link_count` | Float | Count of cross-case co-occurrences |
| 25 | `has_cross_case_link` | Float | Binary (1.0 if accounts appear in other complaints) |

---

### 4.2 Model A: Future Cash-Out Occurrence Classifier

- **Architecture**: `Pipeline(SimpleImputer(strategy="median"), RandomForestClassifier(n_estimators=100, random_state=42))`
- **Artifact Path**: `models/occurrence_baseline.joblib`
- **Evaluation Split**: 80% Train ($N=4,000$), 20% Test ($N=1,000$), Seed 42
- **Verified Test Metrics**:
  - **Accuracy**: $86.16\%$
  - **ROC-AUC**: $0.8617$
  - **PR-AUC**: $0.9569$
  - **Brier Score**: $0.1245$ (Well-calibrated probability curve)
  - **Expected Calibration Error (ECE)**: $0.0573$
- **Risk Tier Thresholds**:
  - `LOW`: Probability $< 0.30$
  - `MODERATE`: Probability $[0.30, 0.60)$
  - `HIGH`: Probability $[0.60, 0.85)$
  - `CRITICAL`: Probability $\ge 0.85$
- **Operational Policy**: **Approved for Active Production Use**.

---

### 4.3 Model B: Candidate Location Prioritizer & Rejection Forensic

- **Operational Baseline**: **Distance-Based Proximity Fallback Heuristic**.
- **Sorting Logic**: `distance_from_account_km ASC`, `historical_cashout_count DESC`.
- **Verified Performance**: **71.73% Top-1 Accuracy** on test candidate sets.
- **Forensic Rejection of `models/location_baseline.joblib`**:
  - *The Learned Model*: A Random Forest classifier was trained on candidate location pairs.
  - *The Artifact*: In the synthetic data generator, candidate generation injected random distant ATMs for cases that were positive cashout targets.
  - *The Statistical Flaw*: This created a synthetic artifact where $P(\text{Target} = 1 \mid \text{Distance} > 50\text{km}) = 88.74\%$, causing the tree to learn that distant ATMs were more likely to be cashout locations.
  - *The Architectural Decision*: To avoid catastrophic failure in real-world deployment, the Random Forest location ranker was **permanently rejected**. The system strictly enforces the distance-based fallback heuristic.

---

### 4.4 Model C: Cash-Out Timing Regressor

- **Architecture**: `Pipeline(SimpleImputer(strategy="median"), RandomForestRegressor(n_estimators=100, random_state=42))`
- **Artifact Path**: `models/timing_baseline.joblib`
- **Target Variable**: `actual_minutes_until_cashout`
- **Verified Performance**: **41.83 min MAE, $R^2 \approx 0.00$**.
- **Forensic Justification**:
  - In the synthetic generation engine, the delay between complaint registration and cashout was drawn from $\text{Uniform}(10, 180\text{ minutes})$ independently of case features.
  - The theoretical expected MAE for a uniform distribution $\text{Uniform}(a, b)$ is $(b - a) / 4 = (180 - 10) / 4 = 42.50\text{ minutes}$.
  - The observed MAE of $41.83\text{ minutes}$ proves the regressor correctly learned the distribution mean, but cannot predict individual variance because no feature signal exists in the synthetic data.
- **Operational Policy**: Deployed as an **Experimental Baseline with High Uncertainty Disclosures**.

---

### 4.5 Decision Support Explanation Engine

The explanation engine dynamically compiles evidence into structured narrative fields:
1. **Summary**: High-level risk statement with probability and predicted risk tier.
2. **Key Risk Factors**: Specific observable patterns that increase risk (e.g., rapid transfer flag active, presence of known mule accounts, multiple cross-case links).
3. **Protective Factors**: Observable patterns that reduce risk (e.g., long complaint delay, established account ages, absence of multi-hop dispersion).
4. **Recommended Actions**: Tactical law enforcement steps (e.g., issue emergency freeze notice on Layer 1 accounts, notify nodal bank officers at Top-1 ATM).

---

### 4.6 Prediction Persistence & Provenance

Every inference execution creates an immutable `PredictionRecord` in the database:
- `prediction_id`: Unique identifier (`PRED_...`)
- `case_id`: Linked complaint
- `occurrence_probability`: Model A score
- `risk_tier`: Assigned tier
- `estimated_minutes`: Model C estimate
- `model_versions`: JSON metadata of all model artifact versions and paths
- `features_used`: Complete 26-feature point-in-time dictionary
- `ranked_locations`: Top-ranked candidate location list
- `narrative`: Full text explanation and risk factor breakdown
- `created_at`: Timestamp of inference run

---

**Last Updated**: 2026-09-28  
**Documentation Version**: 2.0  
**Status**: Constraints Formally Verified
