"""Schema and Structural Validation Module for CASHNET Datasets."""

from typing import Any, Dict, List, Tuple


EXPECTED_TABLE_COLUMNS: Dict[str, List[str]] = {
    "accounts": [
        "account_id", "account_type", "account_opened_at", "account_age_days",
        "home_location_id", "account_status", "baseline_transaction_count",
        "baseline_monthly_inflow", "baseline_monthly_outflow",
        "synthetic_profile_type", "created_at"
    ],
    "complaints": [
        "case_id", "victim_account_id", "fraud_type", "fraud_channel",
        "fraud_amount", "fraud_currency", "fraud_occurred_at",
        "complaint_registered_at", "complaint_delay_minutes", "victim_location_id",
        "initial_transaction_id", "complaint_status", "synthetic_description", "created_at"
    ],
    "transactions": [
        "transaction_id", "case_id", "from_account_id", "to_account_id",
        "amount", "currency", "transaction_type", "channel",
        "transaction_status", "initiated_at", "completed_at", "location_id",
        "is_fraud_linked", "synthetic_event_group_id", "created_at"
    ],
    "locations": [
        "location_id", "location_name", "location_type", "city", "region",
        "latitude", "longitude", "area_cluster_id", "synthetic_location_group",
        "is_active", "created_at"
    ],
    "cashout_events": [
        "cashout_event_id", "case_id", "account_id", "location_id",
        "transaction_id", "withdrawal_amount", "cashout_occurred_at",
        "minutes_since_previous_transaction", "is_future_ground_truth",
        "synthetic_event_group_id", "created_at"
    ],
    "account_labels": [
        "account_id", "is_synthetic_mule", "synthetic_behaviour_type",
        "label_generation_reason", "label_created_at"
    ],
    "prediction_snapshots": [
        "snapshot_id", "case_id", "account_id", "prediction_timestamp",
        "complaint_delay_minutes", "minutes_since_last_transaction",
        "incoming_transaction_count_1h", "outgoing_transaction_count_1h",
        "incoming_transaction_count_24h", "outgoing_transaction_count_24h",
        "total_inflow_24h", "total_outflow_24h", "estimated_remaining_amount",
        "unique_incoming_sources_24h", "linked_account_count", "linked_case_count",
        "historical_cashout_count", "nearest_location_distance_km",
        "hour_of_day", "day_of_week", "account_risk_score", "prediction_mode", "created_at"
    ],
    "location_candidates": [
        "candidate_id", "snapshot_id", "location_id", "distance_from_account_km",
        "historical_cashout_count", "historical_case_count",
        "historical_location_risk", "candidate_rank_reference", "created_at"
    ],
    "case_relationships": [
        "relationship_id", "case_id", "related_case_id", "account_id",
        "relationship_type", "shared_transaction_count", "shared_account_count",
        "relationship_created_at"
    ],
    "case_features": [
        "case_id", "fraud_amount", "complaint_delay_minutes", "transaction_count",
        "unique_account_count", "network_depth", "network_branching_factor",
        "cashout_count", "total_cashout_amount", "distinct_cashout_locations",
        "average_transaction_amount", "max_transaction_amount",
        "synthetic_pattern_type", "created_at"
    ],
    "prediction_ground_truth": [
        "ground_truth_id", "snapshot_id", "actual_next_cashout_event_id",
        "actual_next_location_id", "actual_next_cashout_at",
        "actual_minutes_until_cashout", "actual_cashout_amount",
        "has_future_cashout", "evaluation_status"
    ],
}


def validate_table_structure(table_name: str, records: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Validates presence of required columns, non-null primary keys, and data types.

    Args:
        table_name: Name of table.
        records: List of dictionary records.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors: List[str] = []
    expected_cols = EXPECTED_TABLE_COLUMNS.get(table_name)
    if not expected_cols:
        return False, [f"Unknown table: {table_name}"]

    if not records:
        return False, [f"Table {table_name} is empty."]

    # Check columns in first record
    first_row = records[0]
    missing_cols = [col for col in expected_cols if col not in first_row]
    if missing_cols:
        errors.append(f"Table {table_name} missing required columns: {missing_cols}")

    # Check primary key uniqueness
    pk_col_map = {
        "accounts": "account_id",
        "complaints": "case_id",
        "transactions": "transaction_id",
        "locations": "location_id",
        "cashout_events": "cashout_event_id",
        "account_labels": "account_id",
        "prediction_snapshots": "snapshot_id",
        "location_candidates": "candidate_id",
        "case_relationships": "relationship_id",
        "case_features": "case_id",
        "prediction_ground_truth": "ground_truth_id",
    }

    pk_col = pk_col_map.get(table_name)
    if pk_col:
        seen_pks = set()
        duplicates = []
        for row in records:
            pk_val = row.get(pk_col)
            if pk_val is None:
                errors.append(f"Null primary key in {table_name}.{pk_col}")
            elif pk_val in seen_pks:
                duplicates.append(pk_val)
            seen_pks.add(pk_val)

        if duplicates:
            errors.append(f"Duplicate primary keys in {table_name}.{pk_col}: {duplicates[:5]} (total {len(duplicates)})")

    return len(errors) == 0, errors
