"""Case Forensic Feature Extraction Module for CASHNET Case Similarity."""

from typing import Any, Dict, List


def extract_case_features(
    complaint: Dict[str, Any],
    case_transactions: List[Dict[str, Any]],
    case_cashouts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Calculates summary structural and financial forensic vector attributes for a case.

    Args:
        complaint: Complaint record.
        case_transactions: Transactions linked to case.
        case_cashouts: Cashouts linked to case.

    Returns:
        Dictionary of case similarity features.
    """
    case_id = complaint["case_id"]
    fraud_amt = float(complaint["fraud_amount"])
    delay_mins = complaint["complaint_delay_minutes"]

    tx_count = len(case_transactions)
    amounts = [float(tx["amount"]) for tx in case_transactions] or [fraud_amt]
    unique_accs = set(
        [complaint["victim_account_id"]] +
        [tx["from_account_id"] for tx in case_transactions] +
        [tx["to_account_id"] for tx in case_transactions if tx["to_account_id"] != "ACC_ATM_TERMINAL"]
    )

    csh_count = len(case_cashouts)
    total_csh_amt = sum(float(c["withdrawal_amount"]) for c in case_cashouts)
    distinct_locs = len(set(c["location_id"] for c in case_cashouts))

    depth = 1 if tx_count <= 1 else (2 if tx_count <= 3 else 3)
    branching = round(float(tx_count) / max(1, depth), 3)

    return {
        "case_id": case_id,
        "fraud_amount": round(fraud_amt, 2),
        "complaint_delay_minutes": delay_mins,
        "transaction_count": tx_count,
        "unique_account_count": len(unique_accs),
        "network_depth": depth,
        "network_branching_factor": branching,
        "cashout_count": csh_count,
        "total_cashout_amount": round(total_csh_amt, 2),
        "distinct_cashout_locations": distinct_locs,
        "average_transaction_amount": round(sum(amounts) / len(amounts), 2),
        "max_transaction_amount": round(max(amounts), 2),
    }
