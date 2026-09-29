"""Data Leakage and Hidden Target Isolation Validation for CASHNET."""

from typing import Any, Dict, List, Set, Tuple


FORBIDDEN_MODEL_INPUT_COLUMNS: Set[str] = {
    "is_synthetic_mule",
    "has_future_cashout",
    "actual_next_cashout_event_id",
    "actual_next_location_id",
    "actual_next_cashout_at",
    "actual_minutes_until_cashout",
    "actual_cashout_amount",
    "evaluation_status",
}


def validate_anti_leakage(datasets: Dict[str, List[Dict[str, Any]]]) -> Tuple[bool, List[str]]:
    """Validates strict separation of model input features and hidden evaluation ground truth.

    Args:
        datasets: Dictionary mapping table name to list of records.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors: List[str] = []

    model_input_tables = [
        "prediction_snapshots",
        "location_candidates",
        "case_features",
    ]

    for table_name in model_input_tables:
        records = datasets.get(table_name, [])
        if not records:
            continue

        first_row = records[0]
        present_cols = set(first_row.keys())
        leaked_cols = present_cols.intersection(FORBIDDEN_MODEL_INPUT_COLUMNS)

        if leaked_cols:
            errors.append(
                f"CRITICAL LEAKAGE DETECTED: Model input table '{table_name}' contains target/evaluation columns: {leaked_cols}"
            )

    return len(errors) == 0, errors
