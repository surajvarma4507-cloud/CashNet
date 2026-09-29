"""Relational, Foreign-Key, Candidate Coverage, and Financial Integrity Validation for CASHNET."""

from typing import Any, Dict, List, Tuple


def validate_relational_integrity(datasets: Dict[str, List[Dict[str, Any]]]) -> Tuple[bool, List[str]]:
    """Validates that all foreign key references resolve, no self transfers exist, and candidate coverage holds.

    Args:
        datasets: Dictionary mapping table name to list of records.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors: List[str] = []

    accounts = datasets.get("accounts", [])
    complaints = datasets.get("complaints", [])
    transactions = datasets.get("transactions", [])
    locations = datasets.get("locations", [])
    cashout_events = datasets.get("cashout_events", [])
    snapshots = datasets.get("prediction_snapshots", [])
    candidates = datasets.get("location_candidates", [])
    case_relationships = datasets.get("case_relationships", [])
    case_features = datasets.get("case_features", [])
    ground_truth = datasets.get("prediction_ground_truth", [])

    account_ids = set(a["account_id"] for a in accounts)
    location_ids = set(l["location_id"] for l in locations)
    case_ids = set(c["case_id"] for c in complaints)
    txn_ids = set(t["transaction_id"] for t in transactions)
    cashout_ids = set(c["cashout_event_id"] for c in cashout_events)
    snapshot_ids = set(s["snapshot_id"] for s in snapshots)

    # Map candidate locations per snapshot
    snapshot_candidates_map: Dict[str, List[str]] = {}
    for cand in candidates:
        s_id = cand.get("snapshot_id")
        loc_id = cand.get("location_id")
        if s_id and loc_id:
            snapshot_candidates_map.setdefault(s_id, []).append(loc_id)

    # 1. Check complaints
    for c in complaints:
        if c["victim_account_id"] not in account_ids:
            errors.append(f"Complaint {c['case_id']} victim_account_id '{c['victim_account_id']}' not in accounts.")
        if c.get("victim_location_id") and c["victim_location_id"] not in location_ids:
            errors.append(f"Complaint {c['case_id']} victim_location_id '{c['victim_location_id']}' not in locations.")
        if float(c["fraud_amount"]) <= 0:
            errors.append(f"Complaint {c['case_id']} non-positive fraud_amount {c['fraud_amount']}.")

    # 2. Check transactions & financial constraints
    for t in transactions:
        if t["from_account_id"] not in account_ids:
            errors.append(f"Transaction {t['transaction_id']} from_account_id '{t['from_account_id']}' not in accounts.")
        if t["to_account_id"] not in account_ids:
            errors.append(f"Transaction {t['transaction_id']} to_account_id '{t['to_account_id']}' not in accounts.")
        if t["from_account_id"] == t["to_account_id"]:
            errors.append(f"Transaction {t['transaction_id']} self-transfer detected: from '{t['from_account_id']}' to '{t['to_account_id']}'.")
        if float(t["amount"]) <= 0:
            errors.append(f"Transaction {t['transaction_id']} non-positive amount {t['amount']}.")
        if t.get("case_id") and t["case_id"] not in case_ids:
            errors.append(f"Transaction {t['transaction_id']} case_id '{t['case_id']}' not in complaints.")
        if t.get("location_id") and t["location_id"] not in location_ids:
            errors.append(f"Transaction {t['transaction_id']} location_id '{t['location_id']}' not in locations.")

    # 3. Check cashout_events
    for csh in cashout_events:
        if csh["case_id"] not in case_ids:
            errors.append(f"Cashout {csh['cashout_event_id']} case_id '{csh['case_id']}' not in complaints.")
        if csh["account_id"] not in account_ids:
            errors.append(f"Cashout {csh['cashout_event_id']} account_id '{csh['account_id']}' not in accounts.")
        if csh["location_id"] not in location_ids:
            errors.append(f"Cashout {csh['cashout_event_id']} location_id '{csh['location_id']}' not in locations.")
        if csh["transaction_id"] not in txn_ids:
            errors.append(f"Cashout {csh['cashout_event_id']} transaction_id '{csh['transaction_id']}' not in transactions.")
        if float(csh["withdrawal_amount"]) <= 0:
            errors.append(f"Cashout {csh['cashout_event_id']} non-positive withdrawal_amount {csh['withdrawal_amount']}.")

    # 4. Check snapshots
    for s in snapshots:
        if s["case_id"] not in case_ids:
            errors.append(f"Snapshot {s['snapshot_id']} case_id '{s['case_id']}' not in complaints.")
        if s["account_id"] not in account_ids:
            errors.append(f"Snapshot {s['snapshot_id']} account_id '{s['account_id']}' not in accounts.")

    # 5. Check candidates
    for cand in candidates:
        if cand["snapshot_id"] not in snapshot_ids:
            errors.append(f"Candidate {cand['candidate_id']} snapshot_id '{cand['snapshot_id']}' not in snapshots.")
        if cand["location_id"] not in location_ids:
            errors.append(f"Candidate {cand['candidate_id']} location_id '{cand['location_id']}' not in locations.")
        if float(cand["distance_from_account_km"]) < 0:
            errors.append(f"Candidate {cand['candidate_id']} negative distance {cand['distance_from_account_km']}.")

    # 6. Check ground truth & candidate coverage
    for gt in ground_truth:
        s_id = gt["snapshot_id"]
        if s_id not in snapshot_ids:
            errors.append(f"Ground truth {gt['ground_truth_id']} snapshot_id '{s_id}' not in snapshots.")

        actual_loc = gt.get("actual_next_location_id")
        if actual_loc:
            if actual_loc not in location_ids:
                errors.append(f"Ground truth {gt['ground_truth_id']} actual_next_location_id '{actual_loc}' not in locations.")

            # Candidate Coverage Enforcement:
            # For every snapshot with a positive future cash-out, the actual location MUST be among candidates!
            cand_locs = snapshot_candidates_map.get(s_id, [])
            if actual_loc not in cand_locs:
                errors.append(
                    f"CANDIDATE COVERAGE ERROR: Snapshot '{s_id}' future cashout location '{actual_loc}' is missing from its candidate locations list!"
                )

        if gt.get("actual_next_cashout_event_id") and gt["actual_next_cashout_event_id"] not in cashout_ids:
            errors.append(f"Ground truth {gt['ground_truth_id']} actual_next_cashout_event_id '{gt['actual_next_cashout_event_id']}' not in cashout_events.")

    # 7. Check case relationships & features
    for rel in case_relationships:
        if rel["case_id"] not in case_ids:
            errors.append(f"Case relationship {rel['relationship_id']} case_id '{rel['case_id']}' not in complaints.")
        if rel["related_case_id"] not in case_ids:
            errors.append(f"Case relationship {rel['relationship_id']} related_case_id '{rel['related_case_id']}' not in complaints.")

    for cf in case_features:
        if cf["case_id"] not in case_ids:
            errors.append(f"Case feature case_id '{cf['case_id']}' not in complaints.")

    return len(errors) == 0, errors
