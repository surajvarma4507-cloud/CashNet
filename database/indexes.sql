-- CASHNET Database Indexes (PostgreSQL Compatible / Standard SQL)
-- Optimized for high-speed graph traversal, geospatial lookups, and point-in-time forensic querying

-- Indexes on accounts
CREATE INDEX IF NOT EXISTS idx_accounts_home_location ON accounts(home_location_id);
CREATE INDEX IF NOT EXISTS idx_accounts_type_status ON accounts(account_type, account_status);
CREATE INDEX IF NOT EXISTS idx_accounts_profile_type ON accounts(synthetic_profile_type);

-- Indexes on complaints
CREATE INDEX IF NOT EXISTS idx_complaints_victim_acc ON complaints(victim_account_id);
CREATE INDEX IF NOT EXISTS idx_complaints_registered_at ON complaints(complaint_registered_at);
CREATE INDEX IF NOT EXISTS idx_complaints_fraud_occurred ON complaints(fraud_occurred_at);
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(complaint_status);

-- Indexes on transactions
CREATE INDEX IF NOT EXISTS idx_txns_from_acc ON transactions(from_account_id);
CREATE INDEX IF NOT EXISTS idx_txns_to_acc ON transactions(to_account_id);
CREATE INDEX IF NOT EXISTS idx_txns_case_id ON transactions(case_id);
CREATE INDEX IF NOT EXISTS idx_txns_completed_at ON transactions(completed_at);
CREATE INDEX IF NOT EXISTS idx_txns_initiated_at ON transactions(initiated_at);
CREATE INDEX IF NOT EXISTS idx_txns_from_completed ON transactions(from_account_id, completed_at);
CREATE INDEX IF NOT EXISTS idx_txns_to_completed ON transactions(to_account_id, completed_at);
CREATE INDEX IF NOT EXISTS idx_txns_event_group ON transactions(synthetic_event_group_id);
CREATE INDEX IF NOT EXISTS idx_txns_fraud_linked ON transactions(is_fraud_linked);

-- Indexes on locations
CREATE INDEX IF NOT EXISTS idx_locations_cluster ON locations(area_cluster_id);
CREATE INDEX IF NOT EXISTS idx_locations_city_region ON locations(city, region);
CREATE INDEX IF NOT EXISTS idx_locations_coords ON locations(latitude, longitude);

-- Indexes on cashout_events
CREATE INDEX IF NOT EXISTS idx_cashout_case_id ON cashout_events(case_id);
CREATE INDEX IF NOT EXISTS idx_cashout_account_id ON cashout_events(account_id);
CREATE INDEX IF NOT EXISTS idx_cashout_location_id ON cashout_events(location_id);
CREATE INDEX IF NOT EXISTS idx_cashout_occurred_at ON cashout_events(cashout_occurred_at);
CREATE INDEX IF NOT EXISTS idx_cashout_is_future ON cashout_events(is_future_ground_truth);

-- Indexes on prediction_snapshots
CREATE INDEX IF NOT EXISTS idx_snapshots_case_id ON prediction_snapshots(case_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_account_id ON prediction_snapshots(account_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON prediction_snapshots(prediction_timestamp);
CREATE INDEX IF NOT EXISTS idx_snapshots_mode ON prediction_snapshots(prediction_mode);

-- Indexes on location_candidates
CREATE INDEX IF NOT EXISTS idx_candidates_snapshot_id ON location_candidates(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_candidates_location_id ON location_candidates(location_id);

-- Indexes on case_relationships
CREATE INDEX IF NOT EXISTS idx_case_rel_case ON case_relationships(case_id);
CREATE INDEX IF NOT EXISTS idx_case_rel_related_case ON case_relationships(related_case_id);
CREATE INDEX IF NOT EXISTS idx_case_rel_account ON case_relationships(account_id);

-- Indexes on prediction_ground_truth
CREATE INDEX IF NOT EXISTS idx_ground_truth_snapshot ON prediction_ground_truth(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_ground_truth_has_future ON prediction_ground_truth(has_future_cashout);
