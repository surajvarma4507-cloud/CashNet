# CASHNET Synthetic Financial Data Dictionary (V2)

> **SIH26184 — AI-Powered Cybercrime Cash-Out Prediction & Intervention Platform**  
> *Complete schema, column definitions, foreign keys, constraints, and data-leakage classification for V2.*

---

## Dataset Classification Summary

| Dataset Name | Relative Path (V2) | Category | Primary Key | Foreign Keys | Role in ML Pipeline |
|---|---|---|---|---|---|
| **accounts** | `data_v2/raw/accounts.csv` | Raw Relational | `account_id` | `home_location_id` | Base entity registry |
| **complaints** | `data_v2/raw/complaints.csv` | Raw Relational | `case_id` | `victim_account_id`, `victim_location_id` | Incident trigger records |
| **transactions** | `data_v2/raw/transactions.csv` | Raw Relational | `transaction_id` | `case_id`, `from_account_id`, `to_account_id`, `location_id` | Full money trail ledger |
| **locations** | `data_v2/raw/locations.csv` | Raw Relational | `location_id` | None | Indian ATM & branch spatial registry |
| **cashout_events** | `data_v2/raw/cashout_events.csv` | Raw Relational | `cashout_event_id` | `case_id`, `account_id`, `location_id`, `transaction_id` | Cash withdrawal ledger |
| **account_labels** | `data_v2/raw/account_labels.csv` | Ground Truth | `account_id` | `account_id` | Training target for Mule Classification |
| **case_relationships** | `data_v2/raw/case_relationships.csv` | Raw Graph | `relationship_id` | `case_id`, `related_case_id`, `account_id` | Network similarity & graph analysis |
| **prediction_snapshots** | `data_v2/processed/prediction_snapshots.csv` | Processed Input | `snapshot_id` | `case_id`, `account_id` | Point-in-time features for Cashout Predictor |
| **location_candidates** | `data_v2/processed/location_candidates.csv` | Processed Input | `candidate_id` | `snapshot_id`, `location_id` | Candidate ranking for Spatial Dispatch |
| **case_features** | `data_v2/processed/case_features.csv` | Processed Input | `case_id` | `case_id` | Point-in-time forensic case similarity vector |
| **prediction_ground_truth** | `data_v2/evaluation/prediction_ground_truth.csv` | Hidden Evaluation | `ground_truth_id` | `snapshot_id`, `actual_next_cashout_event_id`, `actual_next_location_id` | Isolated evaluation-only test labels |

---

## 1. `accounts.csv` (Raw Entity Table)

Represents synthetic Indian bank accounts, merchant current accounts, wallets, and intermediary routing nodes.

| Column | Type | Constraints | Description | Permitted for Model Input? |
|---|---|---|---|---|
| `account_id` | VARCHAR(64) | PRIMARY KEY | Unique synthetic account identifier (e.g., `ACC_IND_000001`, `ACC_BUS_000042`) | Yes (ID / Lookup) |
| `account_type` | VARCHAR(32) | NOT NULL, CHECK in (`individual`, `business`, `wallet`, `intermediary`) | Functional account classification | Yes |
| `account_opened_at` | TIMESTAMP | NOT NULL | ISO 8601 UTC timestamp of account creation | Yes |
| `account_age_days` | INTEGER | NOT NULL, >= 0 | Account age in days at simulation start | Yes |
| `home_location_id` | VARCHAR(64) | NULLABLE, FK -> `locations.location_id` | Primary branch / home location of the account holder | Yes |
| `account_status` | VARCHAR(32) | NOT NULL, CHECK in (`active`, `dormant`, `restricted`, `closed`) | Current regulatory/operational state | Yes |
| `baseline_transaction_count` | INTEGER | NOT NULL, >= 0 | Typical monthly transactions baseline | Yes |
| `baseline_monthly_inflow` | NUMERIC(15, 2) | NOT NULL, >= 0.00 | Typical baseline monthly inflow in INR | Yes |
| `baseline_monthly_outflow` | NUMERIC(15, 2) | NOT NULL, >= 0.00 | Typical baseline monthly outflow in INR | Yes |
| `synthetic_profile_type` | VARCHAR(64) | NOT NULL, CHECK in (`normal`, `high_volume`, `intermediary`, `synthetic_mule_candidate`) | Generator behavioral scenario profile | **NO (Audit/Gen Only - Leakage Risk)** |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp | Metadata |

---

## 2. `complaints.csv` (Cybercrime Incident Table)

Represents reported cybercrime incidents registered via National Cybercrime Portal (NCRP / 1930).

| Column | Type | Constraints | Description | Permitted for Model Input? |
|---|---|---|---|---|
| `case_id` | VARCHAR(64) | PRIMARY KEY | Unique case identifier (e.g., `CASE_2026_00001`) | Yes (ID / Lookup) |
| `complaint_number` | VARCHAR(64) | NOT NULL, UNIQUE | NCRP 1930 Acknowledgment Number | Yes |
| `victim_account_id` | VARCHAR(64) | NOT NULL, FK -> `accounts.account_id` | Account from which victim funds were siphoned | Yes |
| `fraud_type` | VARCHAR(64) | NOT NULL, CHECK in (`upi_fraud`, `phishing`, `social_engineering`, `investment_scam`, `remote_access_scam`, `account_takeover`, `digital_arrest_scam`, `loan_app_extortion`) | Categorized cybercrime modus operandi | Yes |
| `fraud_channel` | VARCHAR(32) | NOT NULL, CHECK in (`UPI`, `IMPS`, `NEFT`, `RTGS`, `wallet`, `card`) | Payment rail used for initial unauthorized debit | Yes |
| `fraud_amount` | NUMERIC(15, 2) | NOT NULL, > 0.00 | Total stolen amount in INR | Yes |
| `fraud_currency` | VARCHAR(8) | NOT NULL, DEFAULT 'INR' | Currency code | Yes |
| `fraud_occurred_at` | TIMESTAMP | NOT NULL | Exact time victim was defrauded | Yes |
| `complaint_registered_at` | TIMESTAMP | NOT NULL, >= `fraud_occurred_at` | Time complaint was officially registered | Yes |
| `complaint_delay_minutes` | INTEGER | NOT NULL, >= 0 | Reporting latency in minutes | Yes |
| `victim_location_id` | VARCHAR(64) | NULLABLE, FK -> `locations.location_id` | Location where victim resides | Yes |
| `initial_transaction_id` | VARCHAR(64) | NULLABLE, FK -> `transactions.transaction_id` | First fraudulent transaction link | Yes |
| `complaint_status` | VARCHAR(32) | NOT NULL, CHECK in (`registered`, `under_investigation`, `frozen`, `closed`) | Law enforcement status | Yes |
| `synthetic_description` | TEXT | NOT NULL | Narrative incident description in Indian cybercrime context | Yes (NLP / Search) |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp | Metadata |

---

## 3. `transactions.csv` (Synthetic Money Trail Ledger)

Chronological record of legitimate and fraudulent fund movements across the synthetic financial ecosystem.

| Column | Type | Constraints | Description | Permitted for Model Input? |
|---|---|---|---|---|
| `transaction_id` | VARCHAR(64) | PRIMARY KEY | Unique transaction ID (e.g., `TXN_0000001`) | Yes (ID) |
| `case_id` | VARCHAR(64) | NULLABLE, FK -> `complaints.case_id` | Linked fraud case ID (NULL for legitimate background transactions) | Yes (when t <= snapshot_ts) |
| `from_account_id` | VARCHAR(64) | NOT NULL, FK -> `accounts.account_id` | Source account | Yes (when t <= snapshot_ts) |
| `to_account_id` | VARCHAR(64) | NOT NULL, FK -> `accounts.account_id`, != `from_account_id` | Beneficiary account | Yes (when t <= snapshot_ts) |
| `amount` | NUMERIC(15, 2) | NOT NULL, > 0.00 | Transferred amount in INR | Yes (when t <= snapshot_ts) |
| `currency` | VARCHAR(8) | NOT NULL, DEFAULT 'INR' | Currency | Yes |
| `transaction_type` | VARCHAR(32) | NOT NULL, CHECK in (`transfer`, `withdrawal`, `deposit`, `refund`) | Transaction type | Yes (when t <= snapshot_ts) |
| `channel` | VARCHAR(32) | NOT NULL, CHECK in (`UPI`, `IMPS`, `NEFT`, `RTGS`, `ATM`, `wallet`, `card`) | Indian payment rail | Yes (when t <= snapshot_ts) |
| `transaction_status` | VARCHAR(32) | NOT NULL, CHECK in (`completed`, `pending`, `failed`, `reversed`) | Transaction outcome | Yes (when t <= snapshot_ts) |
| `initiated_at` | TIMESTAMP | NOT NULL | Timestamp transfer initiated | Yes (when t <= snapshot_ts) |
| `completed_at` | TIMESTAMP | NOT NULL, >= `initiated_at` | Timestamp transfer completed | Yes (when t <= snapshot_ts) |
| `location_id` | VARCHAR(64) | NULLABLE, FK -> `locations.location_id` | Originating location | Yes (when t <= snapshot_ts) |
| `is_fraud_linked` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether part of a fraud case | Yes (when t <= snapshot_ts) |
| `synthetic_event_group_id` | VARCHAR(64) | NOT NULL | Group identifier | Traceability |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp | Metadata |

---

## 4. `locations.csv` (Indian ATM & Infrastructure Registry)

Synthetic physical cash dispensing nodes and branch infrastructure across Indian metropolitan clusters (MMR, NCR, Bengaluru, Hyderabad, Kolkata, Pune, Chennai, Ahmedabad/GIFT City, Jaipur, Lucknow, Chandigarh, Kochi, Indore).

| Column | Type | Constraints | Description | Permitted for Model Input? |
|---|---|---|---|---|
| `location_id` | VARCHAR(64) | PRIMARY KEY | Unique location ID (e.g., `SYNTH_LOC_0001`) | Yes |
| `location_name` | VARCHAR(128) | NOT NULL | Synthetic name (e.g., `SYNTH_ATM_MUM_BKC_0012`) | Yes |
| `location_type` | VARCHAR(32) | NOT NULL, CHECK in (`atm`, `branch`, `csp_kiosk`, `pos_merchant`) | Infrastructure category | Yes |
| `city` | VARCHAR(64) | NOT NULL | City (e.g., Mumbai, New Delhi, Bengaluru, Hyderabad, Kolkata, Pune, etc.) | Yes |
| `region` | VARCHAR(64) | NOT NULL | State / Union Territory (Maharashtra, Delhi NCR, Karnataka, etc.) | Yes |
| `latitude` | NUMERIC(9, 6) | NOT NULL, 6.0 <= lat <= 38.0 | Plausible Indian latitude | Yes |
| `longitude` | NUMERIC(9, 6) | NOT NULL, 68.0 <= lon <= 98.0 | Plausible Indian longitude | Yes |
| `area_cluster_id` | VARCHAR(64) | NOT NULL | Metropolitan zone cluster ID (e.g., `CLUSTER_MUM_BKC`) | Yes |
| `synthetic_location_group` | VARCHAR(64) | NOT NULL | Geographic zone grouping (`WEST_ZONE_METRO`, etc.) | Yes |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Operational status | Yes |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp | Metadata |

---

## 5. `cashout_events.csv` (Cash Withdrawal Ledger)

Records physical cash withdrawal milestones from ATMs/branches.

| Column | Type | Constraints | Description | Permitted for Model Input? |
|---|---|---|---|---|
| `cashout_event_id` | VARCHAR(64) | PRIMARY KEY | Unique cashout ID (e.g., `CSH_000001`) | Yes (Historical only) |
| `case_id` | VARCHAR(64) | NOT NULL, FK -> `complaints.case_id` | Linked fraud case | Yes (Historical only) |
| `account_id` | VARCHAR(64) | NOT NULL, FK -> `accounts.account_id` | Account from which cash was withdrawn | Yes (Historical only) |
| `location_id` | VARCHAR(64) | NOT NULL, FK -> `locations.location_id` | ATM/Branch where cash was disbursed | Yes (Historical only) |
| `transaction_id` | VARCHAR(64) | NOT NULL, FK -> `transactions.transaction_id` | Linked ATM withdrawal transaction | Yes (Historical only) |
| `withdrawal_amount` | NUMERIC(15, 2) | NOT NULL, > 0.00 | Physical cash amount in INR | Yes (Historical only) |
| `cashout_occurred_at` | TIMESTAMP | NOT NULL | Timestamp of physical withdrawal | Yes (Historical only) |
| `minutes_since_previous_transaction` | INTEGER | NULLABLE | Velocity metric from preceding transfer | Yes (Historical only) |
| `is_future_ground_truth` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether event occurred after complaint registration | **NO (Evaluation Only)** |
| `synthetic_event_group_id` | VARCHAR(64) | NOT NULL | Case event group | Traceability |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp | Metadata |

---

## 6. `account_labels.csv` (Ground Truth for Mule Classification)

Supervised training labels for mule-risk classification models.

| Column | Type | Constraints | Description | Permitted for Model Input? |
|---|---|---|---|---|
| `account_id` | VARCHAR(64) | PRIMARY KEY, FK -> `accounts.account_id` | Evaluated account ID | Lookup ID |
| `is_synthetic_mule` | INTEGER | NOT NULL, CHECK in (0, 1) | **SUPERVISED TARGET LABEL** (1 = Mule, 0 = Legitimate) | **TARGET (Train/Val only)** |
| `synthetic_behaviour_type` | VARCHAR(64) | NOT NULL | Granular behavioral subtype | **NO (Evaluation only)** |
| `label_generation_reason` | VARCHAR(255) | NOT NULL | Explainability rationale | **NO (Audit only)** |
| `label_created_at` | TIMESTAMP | NOT NULL | Timestamp label assigned | Metadata |

---

## 7. `prediction_snapshots.csv` (Point-in-Time Model Input)

Point-in-time investigator state at `prediction_timestamp = complaint_registered_at`. Contains strictly historical features calculated up to snapshot time.

| Column | Type | Constraints | Description | Permitted for Model Input? |
|---|---|---|---|---|
| `snapshot_id` | VARCHAR(64) | PRIMARY KEY | Unique snapshot ID (e.g., `SNAP_000001`) | Yes (ID) |
| `case_id` | VARCHAR(64) | NOT NULL, FK -> `complaints.case_id` | Target case ID | Yes |
| `account_id` | VARCHAR(64) | NOT NULL, FK -> `accounts.account_id` | Suspicious node under evaluation at snapshot time | Yes |
| `prediction_timestamp` | TIMESTAMP | NOT NULL | Cutoff timestamp (No future data used) | Yes |
| `complaint_delay_minutes` | INTEGER | NOT NULL | Latency from fraud occurrence | Yes |
| `minutes_since_last_transaction` | INTEGER | NULLABLE | Latency from latest past transaction | Yes |
| `incoming_transaction_count_1h` | INTEGER | NOT NULL, >= 0 | Past 1-hour incoming transactions count | Yes |
| `outgoing_transaction_count_1h` | INTEGER | NOT NULL, >= 0 | Past 1-hour outgoing transactions count | Yes |
| `incoming_transaction_count_24h`| INTEGER | NOT NULL, >= 0 | Past 24-hour incoming transactions count | Yes |
| `outgoing_transaction_count_24h`| INTEGER | NOT NULL, >= 0 | Past 24-hour outgoing transactions count | Yes |
| `total_inflow_24h` | NUMERIC(15, 2) | NOT NULL | Total INR inflow past 24h | Yes |
| `total_outflow_24h` | NUMERIC(15, 2) | NOT NULL | Total INR outflow past 24h | Yes |
| `estimated_remaining_amount` | NUMERIC(15, 2) | NOT NULL | Point-in-time estimated un-withdrawn INR balance | Yes |
| `unique_incoming_sources_24h` | INTEGER | NOT NULL | Distinct sending accounts in past 24h | Yes |
| `linked_account_count` | INTEGER | NOT NULL | Total linked accounts in known past trail | Yes |
| `linked_case_count` | INTEGER | NOT NULL | Historical cases linked to this node | Yes |
| `historical_cashout_count` | INTEGER | NOT NULL | Previous cashouts prior to snapshot | Yes |
| `nearest_location_distance_km` | NUMERIC(9, 3) | NOT NULL | Haversine distance to nearest ATM in km | Yes |
| `hour_of_day` | INTEGER | NOT NULL, 0 <= h <= 23 | Hour of day of snapshot | Yes |
| `day_of_week` | INTEGER | NOT NULL, 0 <= d <= 6 | Day of week (0=Mon, 6=Sun) | Yes |
| `account_risk_score` | NUMERIC(5, 4) | NOT NULL, 0.0 <= s <= 1.0 | Baseline heuristic risk score | Yes |
| `prediction_mode` | VARCHAR(32) | NOT NULL, CHECK in (`prediction`, `investigation`) | Operational mode for dispatch | Yes |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp | Metadata |

---

## 8. `location_candidates.csv` (Spatial Candidate Ranking)

Evaluates top spatial candidate ATMs for each prediction snapshot.

| Column | Type | Constraints | Description | Permitted for Model Input? |
|---|---|---|---|---|
| `candidate_id` | VARCHAR(64) | PRIMARY KEY | Unique candidate ID (e.g., `CAND_0000001`) | Yes (ID) |
| `snapshot_id` | VARCHAR(64) | NOT NULL, FK -> `prediction_snapshots.snapshot_id` | Linked snapshot | Yes |
| `location_id` | VARCHAR(64) | NOT NULL, FK -> `locations.location_id` | Evaluated ATM / Branch location | Yes |
| `distance_from_account_km` | NUMERIC(9, 3) | NOT NULL | Great-circle Haversine distance in km | Yes |
| `historical_cashout_count` | INTEGER | NOT NULL | Past cash withdrawals at this location | Yes |
| `historical_case_count` | INTEGER | NOT NULL | Past distinct fraud cases at this location | Yes |
| `historical_location_risk` | NUMERIC(5, 4) | NOT NULL | Baseline location historical risk index | Yes |
| `candidate_rank_reference` | INTEGER | NULLABLE | Baseline distance ranking (1 = nearest) | Yes (Distance Rank Baseline) |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp | Metadata |

---

## 9. `prediction_ground_truth.csv` (HIDDEN Evaluation Targets)

> **STRICTLY ISOLATED IN `data_v2/evaluation/` — NEVER EXPOSE TO PREDICTION INFERENCE.**

| Column | Type | Constraints | Description | Permitted for Model Input? |
|---|---|---|---|---|
| `ground_truth_id` | VARCHAR(64) | PRIMARY KEY | Unique ground truth ID (e.g., `GT_000001`) | **NO (Evaluation Only)** |
| `snapshot_id` | VARCHAR(64) | NOT NULL, FK -> `prediction_snapshots.snapshot_id` | Target snapshot | **NO (Evaluation Only)** |
| `actual_next_cashout_event_id`| VARCHAR(64) | NULLABLE, FK -> `cashout_events.cashout_event_id` | Actual cashout event that occurred in future | **NO (Evaluation Only)** |
| `actual_next_location_id` | VARCHAR(64) | NULLABLE, FK -> `locations.location_id` | **GROUND TRUTH LOCATION TARGET** | **NO (Evaluation Only)** |
| `actual_next_cashout_at` | TIMESTAMP | NULLABLE | Timestamp of future withdrawal | **NO (Evaluation Only)** |
| `actual_minutes_until_cashout`| INTEGER | NULLABLE, >= 0 | **GROUND TRUTH TIME TARGET** (Delta in minutes) | **NO (Evaluation Only)** |
| `actual_cashout_amount` | NUMERIC(15, 2) | NULLABLE | Actual withdrawn amount in INR | **NO (Evaluation Only)** |
| `has_future_cashout` | BOOLEAN | NOT NULL | Binary flag indicating if future withdrawal occurred | **NO (Evaluation Only)** |
| `evaluation_status` | VARCHAR(64) | NOT NULL, CHECK in (`withdrawn_future`, `already_withdrawn_past`, `no_cashout_digital_only`, `expired_unwithdrawn`) | Forensic ground-truth category | **NO (Evaluation Only)** |

---

## 10. `case_relationships.csv` (Case Graph Links)

| Column | Type | Constraints | Description | Permitted for Model Input? |
|---|---|---|---|---|
| `relationship_id` | VARCHAR(64) | PRIMARY KEY | Unique relationship ID (e.g., `REL_000001`) | Yes |
| `case_id` | VARCHAR(64) | NOT NULL, FK -> `complaints.case_id` | Source case | Yes |
| `related_case_id` | VARCHAR(64) | NOT NULL, FK -> `complaints.case_id` | Target case | Yes |
| `account_id` | VARCHAR(64) | NOT NULL, FK -> `accounts.account_id` | Shared intermediary account | Yes |
| `relationship_type` | VARCHAR(64) | NOT NULL | Graph link type (`shared_mule_account`) | Yes |
| `shared_transaction_count` | INTEGER | NOT NULL | Count of shared transactions | Yes |
| `shared_account_count` | INTEGER | NOT NULL | Count of common intermediary nodes | Yes |
| `relationship_created_at` | TIMESTAMP | NOT NULL | Timestamp relationship identified | Metadata |

---

## 11. `case_features.csv` (Point-in-Time Forensic Case Vectors)

| Column | Type | Constraints | Description | Permitted for Model Input? |
|---|---|---|---|---|
| `case_id` | VARCHAR(64) | PRIMARY KEY, FK -> `complaints.case_id` | Target case ID | Yes |
| `fraud_amount` | NUMERIC(15, 2) | NOT NULL | Total stolen amount in INR | Yes |
| `complaint_delay_minutes` | INTEGER | NOT NULL | Latency from fraud occurrence in minutes | Yes |
| `transaction_count` | INTEGER | NOT NULL | Transactions in reconstructed case trail up to prediction time | Yes |
| `unique_account_count` | INTEGER | NOT NULL | Distinct accounts participating in trail up to prediction time | Yes |
| `network_depth` | INTEGER | NOT NULL | Longest path from victim to leaf node at prediction time | Yes |
| `network_branching_factor` | NUMERIC(7, 3) | NOT NULL | Ratio of transactions to network depth | Yes |
| `cashout_count` | INTEGER | NOT NULL | Cashout events completed prior to prediction time | Yes |
| `total_cashout_amount` | NUMERIC(15, 2) | NOT NULL | Sum of withdrawn INR prior to prediction time | Yes |
| `distinct_cashout_locations` | INTEGER | NOT NULL | Unique ATM/branch locations used prior to prediction time | Yes |
| `average_transaction_amount` | NUMERIC(15, 2) | NOT NULL | Mean transaction size in INR | Yes |
| `max_transaction_amount` | NUMERIC(15, 2) | NOT NULL | Peak transaction size in INR | Yes |
| `synthetic_pattern_type` | VARCHAR(64) | NOT NULL | Qualitative pattern classification | **NO (Exclude from Similarity Features)** |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp | Metadata |
