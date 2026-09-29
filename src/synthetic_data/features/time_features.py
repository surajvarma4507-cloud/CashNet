"""Time-Window Feature Extraction Module for CASHNET Cash-out Timing Prediction."""

from datetime import datetime
from typing import Any, Dict, List


def extract_time_features(
    as_of_timestamp: datetime,
    past_transactions: List[Dict[str, Any]],
    estimated_remaining_amount: float,
    account_risk_score: float,
) -> Dict[str, Any]:
    """Extracts features for predicting the time-window of cash-out.

    Args:
        as_of_timestamp: Point in time.
        past_transactions: Transactions completed before as_of_timestamp.
        estimated_remaining_amount: Point-in-time remaining un-withdrawn amount.
        account_risk_score: Point-in-time risk score.

    Returns:
        Dictionary of time-window prediction features.
    """
    if past_transactions:
        t_last = max(datetime.fromisoformat(tx["completed_at"].replace("Z", "+00:00")) for tx in past_transactions)
        mins_since_last_tx = max(0, int((as_of_timestamp - t_last).total_seconds() / 60))
    else:
        mins_since_last_tx = 0

    # Velocity: transactions in past 60 mins
    recent_1h = [
        tx for tx in past_transactions
        if (as_of_timestamp - datetime.fromisoformat(tx["completed_at"].replace("Z", "+00:00"))).total_seconds() <= 3600
    ]
    velocity_1h = len(recent_1h)

    return {
        "minutes_since_last_transaction": mins_since_last_tx,
        "recent_transaction_velocity_1h": velocity_1h,
        "estimated_remaining_amount": round(estimated_remaining_amount, 2),
        "account_risk_score": round(account_risk_score, 4),
        "hour_of_day": as_of_timestamp.hour,
        "day_of_week": as_of_timestamp.weekday(),
        "is_night_time": 1 if (as_of_timestamp.hour >= 22 or as_of_timestamp.hour <= 6) else 0,
        "is_weekend": 1 if as_of_timestamp.weekday() >= 5 else 0,
    }
