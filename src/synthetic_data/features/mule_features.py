"""Mule Risk Feature Extraction Module for CASHNET.

Extracts point-in-time forensic features for mule-account risk scoring:
- Incoming/outgoing counts & ratios
- Unique source/destination network degree
- Transaction velocity and holding time
- Inflow/outflow reconciliation
- Cash-out frequency and velocity
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


def extract_mule_features(
    account_id: str,
    as_of_timestamp: datetime,
    transactions: List[Dict[str, Any]],
    cashout_events: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Calculates point-in-time behavioural features for a target account.

    Strictly considers transactions completed_at <= as_of_timestamp.

    Args:
        account_id: ID of the account being evaluated.
        as_of_timestamp: Point-in-time cutoff.
        transactions: Transactions list.
        cashout_events: Optional cashout events list.

    Returns:
        Dictionary of numerical features ready for mule classification.
    """
    # Filter past transactions for this account
    relevant_in = []
    relevant_out = []

    for tx in transactions:
        t_comp = datetime.fromisoformat(tx["completed_at"].replace("Z", "+00:00"))
        if t_comp > as_of_timestamp:
            continue

        if tx["to_account_id"] == account_id:
            relevant_in.append(tx)
        if tx["from_account_id"] == account_id:
            relevant_out.append(tx)

    in_count = len(relevant_in)
    out_count = len(relevant_out)
    in_amounts = [float(tx["amount"]) for tx in relevant_in]
    out_amounts = [float(tx["amount"]) for tx in relevant_out]

    total_inflow = sum(in_amounts)
    total_outflow = sum(out_amounts)
    all_amounts = in_amounts + out_amounts

    avg_amount = sum(all_amounts) / len(all_amounts) if all_amounts else 0.0
    max_amount = max(all_amounts) if all_amounts else 0.0

    unique_sources = len(set(tx["from_account_id"] for tx in relevant_in))
    unique_destinations = len(set(tx["to_account_id"] for tx in relevant_out if tx["to_account_id"] != "ACC_ATM_TERMINAL"))

    inflow_outflow_ratio = (total_outflow / total_inflow) if total_inflow > 0 else 0.0

    # Holding times between consecutive in/out
    holding_times = []
    if relevant_in and relevant_out:
        for t_in in relevant_in:
            dt_in = datetime.fromisoformat(t_in["completed_at"].replace("Z", "+00:00"))
            subsequent_outs = [
                datetime.fromisoformat(t_out["completed_at"].replace("Z", "+00:00"))
                for t_out in relevant_out
                if datetime.fromisoformat(t_out["completed_at"].replace("Z", "+00:00")) >= dt_in
            ]
            if subsequent_outs:
                min_out = min(subsequent_outs)
                holding_times.append((min_out - dt_in).total_seconds() / 60.0)

    avg_holding_time_min = sum(holding_times) / len(holding_times) if holding_times else 0.0
    rapid_onward_ratio = (
        len([h for h in holding_times if h <= 30.0]) / len(holding_times)
        if holding_times else 0.0
    )

    # Cashout events count for this account prior to timestamp
    hist_cashouts = 0
    if cashout_events:
        hist_cashouts = len([
            c for c in cashout_events
            if c["account_id"] == account_id and
            datetime.fromisoformat(c["cashout_occurred_at"].replace("Z", "+00:00")) <= as_of_timestamp
        ])

    return {
        "account_id": account_id,
        "incoming_transaction_count": in_count,
        "outgoing_transaction_count": out_count,
        "unique_source_count": unique_sources,
        "unique_destination_count": unique_destinations,
        "total_inflow": round(total_inflow, 2),
        "total_outflow": round(total_outflow, 2),
        "average_transaction_amount": round(avg_amount, 2),
        "max_transaction_amount": round(max_amount, 2),
        "inflow_outflow_ratio": round(inflow_outflow_ratio, 4),
        "average_holding_time_minutes": round(avg_holding_time_min, 2),
        "rapid_onward_transfer_ratio": round(rapid_onward_ratio, 4),
        "network_degree": unique_sources + unique_destinations,
        "historical_cashout_count": hist_cashouts,
    }
