-- CASHNET Database Schema (PostgreSQL Compatible / Standard SQL)
-- Smart India Hackathon - SIH26184 | AI-Powered Cybercrime Cash-Out Prediction & Intervention Platform
-- Synthetic Financial Data Model for Indian Cybercrime Intelligence

-- ============================================================================
-- 1. LOCATIONS TABLE (Geographic & ATM/Branch Infrastructure)
-- ============================================================================
CREATE TABLE IF NOT EXISTS locations (
    location_id VARCHAR(64) PRIMARY KEY,
    location_name VARCHAR(128) NOT NULL,
    location_type VARCHAR(32) NOT NULL CHECK (location_type IN ('atm', 'branch', 'csp_kiosk', 'pos_merchant')),
    city VARCHAR(64) NOT NULL,
    region VARCHAR(64) NOT NULL,
    latitude NUMERIC(9, 6) NOT NULL CHECK (latitude BETWEEN 6.0 AND 38.0),
    longitude NUMERIC(9, 6) NOT NULL CHECK (longitude BETWEEN 68.0 AND 98.0),
    area_cluster_id VARCHAR(64) NOT NULL,
    synthetic_location_group VARCHAR(64) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. ACCOUNTS TABLE (Synthetic Bank / Wallet Accounts)
-- ============================================================================
CREATE TABLE IF NOT EXISTS accounts (
    account_id VARCHAR(64) PRIMARY KEY,
    account_type VARCHAR(32) NOT NULL CHECK (account_type IN ('individual', 'business', 'wallet', 'intermediary')),
    account_opened_at TIMESTAMP WITH TIME ZONE NOT NULL,
    account_age_days INTEGER NOT NULL CHECK (account_age_days >= 0),
    home_location_id VARCHAR(64) REFERENCES locations(location_id),
    account_status VARCHAR(32) NOT NULL CHECK (account_status IN ('active', 'dormant', 'restricted', 'closed')),
    baseline_transaction_count INTEGER NOT NULL DEFAULT 0 CHECK (baseline_transaction_count >= 0),
    baseline_monthly_inflow NUMERIC(15, 2) NOT NULL DEFAULT 0.00 CHECK (baseline_monthly_inflow >= 0),
    baseline_monthly_outflow NUMERIC(15, 2) NOT NULL DEFAULT 0.00 CHECK (baseline_monthly_outflow >= 0),
    synthetic_profile_type VARCHAR(64) NOT NULL CHECK (synthetic_profile_type IN ('normal', 'high_volume', 'intermediary', 'synthetic_mule_candidate')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. COMPLAINTS TABLE (Reported Cybercrime Incidents)
-- ============================================================================
CREATE TABLE IF NOT EXISTS complaints (
    case_id VARCHAR(64) PRIMARY KEY,
    victim_account_id VARCHAR(64) NOT NULL REFERENCES accounts(account_id),
    fraud_type VARCHAR(64) NOT NULL CHECK (fraud_type IN ('upi_fraud', 'phishing', 'social_engineering', 'investment_scam', 'remote_access_scam', 'account_takeover')),
    fraud_channel VARCHAR(32) NOT NULL CHECK (fraud_channel IN ('UPI', 'IMPS', 'NEFT', 'RTGS', 'wallet', 'card')),
    fraud_amount NUMERIC(15, 2) NOT NULL CHECK (fraud_amount > 0),
    fraud_currency VARCHAR(8) NOT NULL DEFAULT 'INR',
    fraud_occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    complaint_registered_at TIMESTAMP WITH TIME ZONE NOT NULL,
    complaint_delay_minutes INTEGER NOT NULL CHECK (complaint_delay_minutes >= 0),
    victim_location_id VARCHAR(64) REFERENCES locations(location_id),
    initial_transaction_id VARCHAR(64),
    complaint_status VARCHAR(32) NOT NULL CHECK (complaint_status IN ('registered', 'under_investigation', 'frozen', 'closed')),
    synthetic_description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_complaint_time CHECK (complaint_registered_at >= fraud_occurred_at)
);

-- ============================================================================
-- 4. TRANSACTIONS TABLE (Synthetic Money Trail)
-- ============================================================================
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(64) PRIMARY KEY,
    case_id VARCHAR(64) REFERENCES complaints(case_id),
    from_account_id VARCHAR(64) NOT NULL REFERENCES accounts(account_id),
    to_account_id VARCHAR(64) NOT NULL REFERENCES accounts(account_id),
    amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(8) NOT NULL DEFAULT 'INR',
    transaction_type VARCHAR(32) NOT NULL CHECK (transaction_type IN ('transfer', 'withdrawal', 'deposit', 'refund')),
    channel VARCHAR(32) NOT NULL CHECK (channel IN ('UPI', 'IMPS', 'NEFT', 'RTGS', 'ATM', 'wallet', 'card')),
    transaction_status VARCHAR(32) NOT NULL CHECK (transaction_status IN ('completed', 'pending', 'failed', 'reversed')),
    initiated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    location_id VARCHAR(64) REFERENCES locations(location_id),
    is_fraud_linked BOOLEAN NOT NULL DEFAULT FALSE,
    synthetic_event_group_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_no_self_transfer CHECK (from_account_id <> to_account_id),
    CONSTRAINT chk_txn_timing CHECK (completed_at >= initiated_at)
);

-- ============================================================================
-- 5. CASHOUT_EVENTS TABLE (Cash Withdrawal Milestones & Ground Truth)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cashout_events (
    cashout_event_id VARCHAR(64) PRIMARY KEY,
    case_id VARCHAR(64) NOT NULL REFERENCES complaints(case_id),
    account_id VARCHAR(64) NOT NULL REFERENCES accounts(account_id),
    location_id VARCHAR(64) NOT NULL REFERENCES locations(location_id),
    transaction_id VARCHAR(64) NOT NULL REFERENCES transactions(transaction_id),
    withdrawal_amount NUMERIC(15, 2) NOT NULL CHECK (withdrawal_amount > 0),
    cashout_occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    minutes_since_previous_transaction INTEGER,
    is_future_ground_truth BOOLEAN NOT NULL DEFAULT FALSE,
    synthetic_event_group_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 6. ACCOUNT_LABELS TABLE (Synthetic Ground Truth for Mule Classification)
-- ============================================================================
CREATE TABLE IF NOT EXISTS account_labels (
    account_id VARCHAR(64) PRIMARY KEY REFERENCES accounts(account_id),
    is_synthetic_mule INTEGER NOT NULL CHECK (is_synthetic_mule IN (0, 1)),
    synthetic_behaviour_type VARCHAR(64) NOT NULL,
    label_generation_reason VARCHAR(255) NOT NULL,
    label_created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 7. PREDICTION_SNAPSHOTS TABLE (Point-in-time Investigator States)
-- ============================================================================
CREATE TABLE IF NOT EXISTS prediction_snapshots (
    snapshot_id VARCHAR(64) PRIMARY KEY,
    case_id VARCHAR(64) NOT NULL REFERENCES complaints(case_id),
    account_id VARCHAR(64) NOT NULL REFERENCES accounts(account_id),
    prediction_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    complaint_delay_minutes INTEGER NOT NULL,
    minutes_since_last_transaction INTEGER,
    incoming_transaction_count_1h INTEGER NOT NULL DEFAULT 0,
    outgoing_transaction_count_1h INTEGER NOT NULL DEFAULT 0,
    incoming_transaction_count_24h INTEGER NOT NULL DEFAULT 0,
    outgoing_transaction_count_24h INTEGER NOT NULL DEFAULT 0,
    total_inflow_24h NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    total_outflow_24h NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    estimated_remaining_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    unique_incoming_sources_24h INTEGER NOT NULL DEFAULT 0,
    linked_account_count INTEGER NOT NULL DEFAULT 0,
    linked_case_count INTEGER NOT NULL DEFAULT 0,
    historical_cashout_count INTEGER NOT NULL DEFAULT 0,
    nearest_location_distance_km NUMERIC(9, 3) NOT NULL,
    hour_of_day INTEGER NOT NULL CHECK (hour_of_day BETWEEN 0 AND 23),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    account_risk_score NUMERIC(5, 4) NOT NULL CHECK (account_risk_score BETWEEN 0.0 AND 1.0),
    prediction_mode VARCHAR(32) NOT NULL CHECK (prediction_mode IN ('prediction', 'investigation')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 8. LOCATION_CANDIDATES TABLE (Candidate Ranking for Spatial Dispatch)
-- ============================================================================
CREATE TABLE IF NOT EXISTS location_candidates (
    candidate_id VARCHAR(64) PRIMARY KEY,
    snapshot_id VARCHAR(64) NOT NULL REFERENCES prediction_snapshots(snapshot_id),
    location_id VARCHAR(64) NOT NULL REFERENCES locations(location_id),
    distance_from_account_km NUMERIC(9, 3) NOT NULL,
    historical_cashout_count INTEGER NOT NULL DEFAULT 0,
    historical_case_count INTEGER NOT NULL DEFAULT 0,
    historical_location_risk NUMERIC(5, 4) NOT NULL DEFAULT 0.0000,
    candidate_rank_reference INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 9. CASE_RELATIONSHIPS TABLE (Network Graph & Co-occurrence Links)
-- ============================================================================
CREATE TABLE IF NOT EXISTS case_relationships (
    relationship_id VARCHAR(64) PRIMARY KEY,
    case_id VARCHAR(64) NOT NULL REFERENCES complaints(case_id),
    related_case_id VARCHAR(64) NOT NULL REFERENCES complaints(case_id),
    account_id VARCHAR(64) NOT NULL REFERENCES accounts(account_id),
    relationship_type VARCHAR(64) NOT NULL,
    shared_transaction_count INTEGER NOT NULL DEFAULT 1,
    shared_account_count INTEGER NOT NULL DEFAULT 1,
    relationship_created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 10. CASE_FEATURES TABLE (Case Similarity & Forensic Vector Attributes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS case_features (
    case_id VARCHAR(64) PRIMARY KEY REFERENCES complaints(case_id),
    fraud_amount NUMERIC(15, 2) NOT NULL,
    complaint_delay_minutes INTEGER NOT NULL,
    transaction_count INTEGER NOT NULL,
    unique_account_count INTEGER NOT NULL,
    network_depth INTEGER NOT NULL,
    network_branching_factor NUMERIC(7, 3) NOT NULL,
    cashout_count INTEGER NOT NULL,
    total_cashout_amount NUMERIC(15, 2) NOT NULL,
    distinct_cashout_locations INTEGER NOT NULL,
    average_transaction_amount NUMERIC(15, 2) NOT NULL,
    max_transaction_amount NUMERIC(15, 2) NOT NULL,
    synthetic_pattern_type VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 11. PREDICTION_GROUND_TRUTH TABLE (Evaluation-Only Target Outcomes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS prediction_ground_truth (
    ground_truth_id VARCHAR(64) PRIMARY KEY,
    snapshot_id VARCHAR(64) NOT NULL REFERENCES prediction_snapshots(snapshot_id),
    actual_next_cashout_event_id VARCHAR(64) REFERENCES cashout_events(cashout_event_id),
    actual_next_location_id VARCHAR(64) REFERENCES locations(location_id),
    actual_next_cashout_at TIMESTAMP WITH TIME ZONE,
    actual_minutes_until_cashout INTEGER,
    actual_cashout_amount NUMERIC(15, 2),
    has_future_cashout BOOLEAN NOT NULL DEFAULT FALSE,
    evaluation_status VARCHAR(64) NOT NULL CHECK (evaluation_status IN ('withdrawn_future', 'already_withdrawn_past', 'no_cashout_digital_only', 'expired_unwithdrawn'))
);
