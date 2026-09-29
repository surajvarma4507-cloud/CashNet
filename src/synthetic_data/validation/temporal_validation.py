"""Temporal Consistency and Anti-Leakage Timing Validation."""

from datetime import datetime
from typing import Any, Dict, List, Tuple


def validate_temporal_consistency(datasets: Dict[str, List[Dict[str, Any]]]) -> Tuple[bool, List[str]]:
    """Validates chronological order, complaint delays, snapshot boundaries, and future events.

    Args:
        datasets: Dictionary mapping table name to list of records.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors: List[str] = []

    complaints = datasets.get("complaints", [])
    transactions = datasets.get("transactions", [])
    cashouts = datasets.get("cashout_events", [])
    snapshots = datasets.get("prediction_snapshots", [])
    ground_truth = datasets.get("prediction_ground_truth", [])

    # Map snapshot timestamps
    snap_ts_map = {
        s["snapshot_id"]: datetime.fromisoformat(s["prediction_timestamp"].replace("Z", "+00:00"))
        for s in snapshots
    }

    # 1. Validate complaints temporal logic
    for c in complaints:
        t_fraud = datetime.fromisoformat(c["fraud_occurred_at"].replace("Z", "+00:00"))
        t_comp = datetime.fromisoformat(c["complaint_registered_at"].replace("Z", "+00:00"))

        if t_comp < t_fraud:
            errors.append(f"Complaint {c['case_id']}: registered_at ({t_comp}) is before fraud_occurred_at ({t_fraud}).")

        expected_delay = int((t_comp - t_fraud).total_seconds() / 60)
        if abs(c["complaint_delay_minutes"] - expected_delay) > 1:
            errors.append(
                f"Complaint {c['case_id']}: complaint_delay_minutes {c['complaint_delay_minutes']} does not match timestamp difference {expected_delay} mins."
            )

    # 2. Validate transactions timing
    for t in transactions:
        t_init = datetime.fromisoformat(t["initiated_at"].replace("Z", "+00:00"))
        t_comp = datetime.fromisoformat(t["completed_at"].replace("Z", "+00:00"))

        if t_comp < t_init:
            errors.append(f"Transaction {t['transaction_id']}: completed_at ({t_comp}) is before initiated_at ({t_init}).")

    # 3. Validate Ground Truth future vs negative consistency
    for gt in ground_truth:
        snap_id = gt["snapshot_id"]
        t_snap = snap_ts_map.get(snap_id)
        if not t_snap:
            continue

        if gt.get("has_future_cashout"):
            if not gt.get("actual_next_cashout_at"):
                errors.append(f"Ground truth {gt['ground_truth_id']} has_future_cashout=True but actual_next_cashout_at is None.")
            else:
                t_csh = datetime.fromisoformat(gt["actual_next_cashout_at"].replace("Z", "+00:00"))
                if t_csh <= t_snap:
                    errors.append(
                        f"Ground truth {gt['ground_truth_id']}: actual_next_cashout_at ({t_csh}) is not strictly after snapshot timestamp ({t_snap})."
                    )

                expected_mins = int((t_csh - t_snap).total_seconds() / 60)
                if gt.get("actual_minutes_until_cashout") is not None and abs(gt["actual_minutes_until_cashout"] - expected_mins) > 1:
                    errors.append(
                        f"Ground truth {gt['ground_truth_id']}: actual_minutes_until_cashout {gt['actual_minutes_until_cashout']} does not match delta {expected_mins}."
                    )
        else:
            # Negative future cashout assertions
            if gt.get("actual_next_cashout_at") is not None:
                errors.append(f"Ground truth {gt['ground_truth_id']}: has_future_cashout=False but actual_next_cashout_at is not None.")
            if gt.get("actual_next_location_id") is not None:
                errors.append(f"Ground truth {gt['ground_truth_id']}: has_future_cashout=False but actual_next_location_id is not None.")
            if gt.get("actual_next_cashout_event_id") is not None:
                errors.append(f"Ground truth {gt['ground_truth_id']}: has_future_cashout=False but actual_next_cashout_event_id is not None.")
            if gt.get("actual_minutes_until_cashout") is not None:
                errors.append(f"Ground truth {gt['ground_truth_id']}: has_future_cashout=False but actual_minutes_until_cashout is not None.")
            if gt.get("actual_cashout_amount") is not None:
                errors.append(f"Ground truth {gt['ground_truth_id']}: has_future_cashout=False but actual_cashout_amount is not None.")

    return len(errors) == 0, errors
