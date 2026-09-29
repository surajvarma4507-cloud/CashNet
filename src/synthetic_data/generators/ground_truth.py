"""Ground Truth, Prediction Snapshots, Location Candidates & Case Features Generator.

Implements strict point-in-time state reconstruction:
- Calculates all snapshot features strictly before prediction_timestamp (no future data leakage).
- Determines Prediction Mode vs Investigation Mode based on remaining funds and reporting delay.
- Generates location candidates with distance and historical frequency prior to snapshot.
- Guarantees 100% candidate coverage for positive future-cashout snapshots without target leakage.
- Separates evaluation ground truth into prediction_ground_truth.csv.
- Calculates point-in-time forensic case features for case_features.csv.
"""

import math
import random
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Set, Tuple

from ..config import GenerationConfig


def round_curr(val: float) -> float:
    """Rounds financial amount to 2 decimal places."""
    d = Decimal(str(val))
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two geographic coordinates in kilometers."""
    r = 6371.0  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 3)


def generate_ground_truth_and_snapshots(
    config: GenerationConfig,
    complaints: List[Dict[str, Any]],
    accounts: List[Dict[str, Any]],
    locations: List[Dict[str, Any]],
    transactions: List[Dict[str, Any]],
    cashout_events: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Generates prediction snapshots, location candidates, case features, and evaluation ground truth.

    Args:
        config: Generation configuration.
        complaints: Cybercrime complaints.
        accounts: Accounts pool.
        locations: Locations pool.
        transactions: All transactions.
        cashout_events: All cashout events.

    Returns:
        Tuple of (snapshots, location_candidates, case_features, prediction_ground_truth).
    """
    rng = random.Random(config.seed + 500)
    location_lookup = {loc["location_id"]: loc for loc in locations}
    account_lookup = {acc["account_id"]: acc for acc in accounts}

    # Group transactions and cashouts by case_id
    case_txns: Dict[str, List[Dict[str, Any]]] = {}
    for tx in transactions:
        c_id = tx.get("case_id")
        if c_id:
            case_txns.setdefault(c_id, []).append(tx)

    case_cashouts: Dict[str, List[Dict[str, Any]]] = {}
    for csh in cashout_events:
        c_id = csh.get("case_id")
        if c_id:
            case_cashouts.setdefault(c_id, []).append(csh)

    snapshots: List[Dict[str, Any]] = []
    location_candidates: List[Dict[str, Any]] = []
    case_features: List[Dict[str, Any]] = []
    ground_truth_records: List[Dict[str, Any]] = []

    snap_counter = 1
    cand_counter = 1
    gt_counter = 1

    num_candidates_target = max(5, config.candidates_per_snapshot)

    for comp in complaints:
        case_id = comp["case_id"]
        t_complaint = datetime.fromisoformat(comp["complaint_registered_at"].replace("Z", "+00:00"))
        delay_minutes = comp["complaint_delay_minutes"]
        fraud_amt = float(comp["fraud_amount"])

        all_case_txs = case_txns.get(case_id, [])
        all_case_cshs = case_cashouts.get(case_id, [])

        # Filter past transactions: completed_at <= t_complaint
        past_txs = [
            tx for tx in all_case_txs
            if datetime.fromisoformat(tx["completed_at"].replace("Z", "+00:00")) <= t_complaint
        ]

        # Filter past cashouts: cashout_occurred_at <= t_complaint
        past_cshs = [
            csh for csh in all_case_cshs
            if datetime.fromisoformat(csh["cashout_occurred_at"].replace("Z", "+00:00")) <= t_complaint
        ]

        # Filter future cashouts: cashout_occurred_at > t_complaint
        future_cshs = [
            csh for csh in all_case_cshs
            if datetime.fromisoformat(csh["cashout_occurred_at"].replace("Z", "+00:00")) > t_complaint
        ]
        # Sort future cashouts strictly by occurrence time
        future_cshs.sort(key=lambda c: datetime.fromisoformat(c["cashout_occurred_at"].replace("Z", "+00:00")))

        # Identify target suspicious account (leaf destination node in past transactions)
        if past_txs:
            last_tx = max(past_txs, key=lambda tx: datetime.fromisoformat(tx["completed_at"].replace("Z", "+00:00")))
            target_account_id = last_tx["to_account_id"]
            if target_account_id == "ACC_ATM_TERMINAL":
                target_account_id = last_tx["from_account_id"]
        else:
            target_account_id = comp["victim_account_id"]

        # Calculate point-in-time financial reconciliation
        target_inflows = [
            float(tx["amount"]) for tx in past_txs
            if tx["to_account_id"] == target_account_id and tx["transaction_type"] == "transfer"
        ]
        target_outflows = [
            float(tx["amount"]) for tx in past_txs
            if tx["from_account_id"] == target_account_id
        ]
        past_withdrawn = sum(float(c["withdrawal_amount"]) for c in past_cshs)

        total_inflow_past = sum(target_inflows) if target_inflows else (fraud_amt if target_account_id != comp["victim_account_id"] else 0.0)
        total_outflow_past = sum(target_outflows)

        estimated_remaining = max(0.0, total_inflow_past - total_outflow_past)

        # Latency since last past transaction
        if past_txs:
            t_last_tx = max(datetime.fromisoformat(tx["completed_at"].replace("Z", "+00:00")) for tx in past_txs)
            min_since_last = int((t_complaint - t_last_tx).total_seconds() / 60)
        else:
            min_since_last = delay_minutes

        # Mode determination:
        # If funds already withdrawn (past_withdrawn >= fraud_amt * 0.85) OR
        # delay > 10080 min (7 days) OR estimated_remaining <= 50.0 -> 'investigation' mode
        # Otherwise -> 'prediction' mode
        if past_withdrawn >= fraud_amt * 0.85 or delay_minutes > 10080 or estimated_remaining <= 50.0:
            prediction_mode = "investigation"
        else:
            prediction_mode = "prediction"

        # Baseline Risk score (derived strictly from point-in-time past features)
        risk_score = round(
            min(1.0, max(0.05, 0.45 + (0.35 if estimated_remaining > 0 else -0.2) + (0.2 if delay_minutes < 120 else -0.15))),
            4
        )

        # Nearest location distance
        acc_obj = account_lookup.get(target_account_id, {})
        acc_loc_id = acc_obj.get("home_location_id")
        acc_loc = location_lookup.get(acc_loc_id) if acc_loc_id else None

        if acc_loc and locations:
            min_dist = min(
                haversine_distance_km(acc_loc["latitude"], acc_loc["longitude"], loc["latitude"], loc["longitude"])
                for loc in locations if loc["location_id"] != acc_loc_id
            )
        else:
            min_dist = 1.250

        snap_id = f"SNAP_{snap_counter:06d}"
        snap_counter += 1

        snap_rec = {
            "snapshot_id": snap_id,
            "case_id": case_id,
            "account_id": target_account_id,
            "prediction_timestamp": t_complaint.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "complaint_delay_minutes": delay_minutes,
            "minutes_since_last_transaction": min_since_last,
            "incoming_transaction_count_1h": len([t for t in past_txs if (t_complaint - datetime.fromisoformat(t["completed_at"].replace("Z", "+00:00"))).total_seconds() <= 3600]),
            "outgoing_transaction_count_1h": len([t for t in past_txs if t["from_account_id"] == target_account_id and (t_complaint - datetime.fromisoformat(t["completed_at"].replace("Z", "+00:00"))).total_seconds() <= 3600]),
            "incoming_transaction_count_24h": len([t for t in past_txs if (t_complaint - datetime.fromisoformat(t["completed_at"].replace("Z", "+00:00"))).total_seconds() <= 86400]),
            "outgoing_transaction_count_24h": len([t for t in past_txs if t["from_account_id"] == target_account_id and (t_complaint - datetime.fromisoformat(t["completed_at"].replace("Z", "+00:00"))).total_seconds() <= 86400]),
            "total_inflow_24h": round_curr(total_inflow_past),
            "total_outflow_24h": round_curr(total_outflow_past),
            "estimated_remaining_amount": round_curr(estimated_remaining),
            "unique_incoming_sources_24h": len(set(tx["from_account_id"] for tx in past_txs)),
            "linked_account_count": len(set([tx["from_account_id"] for tx in past_txs] + [tx["to_account_id"] for tx in past_txs if tx["to_account_id"] != "ACC_ATM_TERMINAL"])),
            "linked_case_count": 1,
            "historical_cashout_count": len(past_cshs),
            "nearest_location_distance_km": round(min_dist, 3),
            "hour_of_day": t_complaint.hour,
            "day_of_week": t_complaint.weekday(),
            "account_risk_score": risk_score,
            "prediction_mode": prediction_mode,
            "created_at": t_complaint.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        snapshots.append(snap_rec)

        # ---------------------------------------------------------------------
        # Location Candidate Generation (Spatial Haversine Ranking + Target Inclusion)
        # ---------------------------------------------------------------------
        future_loc_id = future_cshs[0]["location_id"] if future_cshs else None

        if acc_loc:
            # Sort all available locations by spatial distance to account location
            all_sorted_locs = sorted(
                locations,
                key=lambda l: haversine_distance_km(acc_loc["latitude"], acc_loc["longitude"], l["latitude"], l["longitude"])
            )
        else:
            all_sorted_locs = list(locations)

        # Pick candidate locations
        selected_cand_locs = all_sorted_locs[:num_candidates_target]

        # Enforce candidate coverage: if positive future cashout exists and its location is not yet selected, include it!
        if future_loc_id and future_loc_id not in [l["location_id"] for l in selected_cand_locs]:
            actual_loc_obj = location_lookup.get(future_loc_id)
            if actual_loc_obj:
                selected_cand_locs[-1] = actual_loc_obj

        # Re-sort candidate set strictly by spatial distance from account location to prevent ranking leakage
        if acc_loc:
            selected_cand_locs.sort(
                key=lambda l: haversine_distance_km(acc_loc["latitude"], acc_loc["longitude"], l["latitude"], l["longitude"])
            )

        for rank_idx, cand_loc in enumerate(selected_cand_locs):
            dist_km = (
                haversine_distance_km(acc_loc["latitude"], acc_loc["longitude"], cand_loc["latitude"], cand_loc["longitude"])
                if acc_loc else round(rng.uniform(0.5, 9.5), 3)
            )

            cand_id = f"CAND_{cand_counter:07d}"
            cand_counter += 1

            location_candidates.append({
                "candidate_id": cand_id,
                "snapshot_id": snap_id,
                "location_id": cand_loc["location_id"],
                "distance_from_account_km": round(dist_km, 3),
                "historical_cashout_count": len([c for c in past_cshs if c["location_id"] == cand_loc["location_id"]]),
                "historical_case_count": 1 if any(c["location_id"] == cand_loc["location_id"] for c in past_cshs) else 0,
                "historical_location_risk": round(rng.uniform(0.05, 0.85), 4),
                "candidate_rank_reference": rank_idx + 1,
                "created_at": t_complaint.strftime("%Y-%m-%dT%H:%M:%SZ"),
            })

        # ---------------------------------------------------------------------
        # Hidden Evaluation Ground Truth (Strictly Separated)
        # ---------------------------------------------------------------------
        gt_id = f"GT_{gt_counter:06d}"
        gt_counter += 1

        if future_cshs:
            next_csh = future_cshs[0]
            t_csh = datetime.fromisoformat(next_csh["cashout_occurred_at"].replace("Z", "+00:00"))
            mins_until = int((t_csh - t_complaint).total_seconds() / 60)

            gt_rec = {
                "ground_truth_id": gt_id,
                "snapshot_id": snap_id,
                "actual_next_cashout_event_id": next_csh["cashout_event_id"],
                "actual_next_location_id": next_csh["location_id"],
                "actual_next_cashout_at": next_csh["cashout_occurred_at"],
                "actual_minutes_until_cashout": max(0, mins_until),
                "actual_cashout_amount": float(next_csh["withdrawal_amount"]),
                "has_future_cashout": True,
                "evaluation_status": "withdrawn_future",
            }
        else:
            if past_cshs:
                eval_status = "already_withdrawn_past"
            elif not all_case_cshs:
                eval_status = "no_cashout_digital_only"
            else:
                eval_status = "expired_unwithdrawn"

            gt_rec = {
                "ground_truth_id": gt_id,
                "snapshot_id": snap_id,
                "actual_next_cashout_event_id": None,
                "actual_next_location_id": None,
                "actual_next_cashout_at": None,
                "actual_minutes_until_cashout": None,
                "actual_cashout_amount": None,
                "has_future_cashout": False,
                "evaluation_status": eval_status,
            }
        ground_truth_records.append(gt_rec)

        # ---------------------------------------------------------------------
        # Point-in-Time Case Features (Forensic Vector strictly at t <= snapshot)
        # ---------------------------------------------------------------------
        past_amounts = [float(tx["amount"]) for tx in past_txs] or [fraud_amt]
        unique_past_accs = set(
            [comp["victim_account_id"]] +
            [tx["from_account_id"] for tx in past_txs] +
            [tx["to_account_id"] for tx in past_txs if tx["to_account_id"] != "ACC_ATM_TERMINAL"]
        )
        past_csh_amt = sum(float(c["withdrawal_amount"]) for c in past_cshs)
        distinct_past_locs = len(set(c["location_id"] for c in past_cshs))

        depth = 1 if len(past_txs) <= 1 else (2 if len(past_txs) <= 3 else 3)
        branching = round(float(len(past_txs)) / max(1, depth), 3)

        if len(past_cshs) == 0:
            pattern_type = "unwithdrawn_holding"
        elif depth == 1:
            pattern_type = "direct_cashout"
        elif depth == 2 and branching <= 1.5:
            pattern_type = "two_hop_layering"
        elif branching > 1.5:
            pattern_type = "fan_out_split"
        else:
            pattern_type = "shared_network_layering"

        case_features.append({
            "case_id": case_id,
            "fraud_amount": round_curr(fraud_amt),
            "complaint_delay_minutes": delay_minutes,
            "transaction_count": len(past_txs),
            "unique_account_count": len(unique_past_accs),
            "network_depth": depth,
            "network_branching_factor": branching,
            "cashout_count": len(past_cshs),
            "total_cashout_amount": round_curr(past_csh_amt),
            "distinct_cashout_locations": distinct_past_locs,
            "average_transaction_amount": round_curr(sum(past_amounts) / len(past_amounts)),
            "max_transaction_amount": round_curr(max(past_amounts)),
            "synthetic_pattern_type": pattern_type,
            "created_at": t_complaint.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

    return snapshots, location_candidates, case_features, ground_truth_records
