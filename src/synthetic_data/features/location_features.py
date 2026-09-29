"""Location Feature Extraction Module for CASHNET Spatial Dispatch."""

import math
from datetime import datetime
from typing import Any, Dict, List, Optional


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates Haversine distance in km."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    return round(r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)), 3)


def extract_location_features(
    account_location: Dict[str, Any],
    candidate_location: Dict[str, Any],
    as_of_timestamp: datetime,
    historical_cashouts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Calculates candidate location spatial and historical features.

    Args:
        account_location: Home/last known location of suspicious account.
        candidate_location: Evaluated candidate location.
        as_of_timestamp: Point in time.
        historical_cashouts: Cashout events list prior to timestamp.

    Returns:
        Dictionary of location candidate features.
    """
    loc_id = candidate_location["location_id"]
    lat1, lon1 = account_location["latitude"], account_location["longitude"]
    lat2, lon2 = candidate_location["latitude"], candidate_location["longitude"]

    dist_km = haversine_km(lat1, lon1, lat2, lon2)

    past_loc_cashouts = [
        c for c in historical_cashouts
        if c["location_id"] == loc_id and
        datetime.fromisoformat(c["cashout_occurred_at"].replace("Z", "+00:00")) <= as_of_timestamp
    ]

    hist_count = len(past_loc_cashouts)
    hist_amount = sum(float(c["withdrawal_amount"]) for c in past_loc_cashouts)
    hist_cases = len(set(c["case_id"] for c in past_loc_cashouts))

    return {
        "location_id": loc_id,
        "distance_from_account_km": dist_km,
        "historical_cashout_count": hist_count,
        "historical_total_withdrawn": round(hist_amount, 2),
        "historical_case_count": hist_cases,
        "hour_of_day": as_of_timestamp.hour,
        "day_of_week": as_of_timestamp.weekday(),
    }
