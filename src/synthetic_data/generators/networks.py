"""Network and Money Trail Generator for CASHNET Synthetic Financial Engine.

Generates realistic fraud money-trails across diverse behavioural scenarios:
- Scenario 1: Single-hop rapid cash-out
- Scenario 2: Two-hop layering (Aggregator -> Terminal)
- Scenario 3: Deep multi-hop layering (3-hop & 4-hop chains)
- Scenario 4: Split-transfer fan-out pattern (1 -> N mules)
- Scenario 5: Multi-location ATM cash-out (distributed withdrawals across ATM nodes)
- Scenario 6: Delayed cash-out (sleeper mule / overnight holding)
- Scenario 7: Shared syndicate mule network (common hub across multiple complaints)
- Scenario 8: Repeated intermediary conduit across multiple cases
- Scenario 9: Digital-only fraud drain (no physical ATM cash-out)
- Scenario 10: Unwithdrawn funds / dormant holding
"""

import math
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Set, Tuple

from ..config import GenerationConfig


def round_curr(val: float) -> float:
    """Rounds financial amount to 2 decimal places using Decimal."""
    d = Decimal(str(val))
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def generate_transaction_networks(
    config: GenerationConfig,
    complaints: List[Dict[str, Any]],
    accounts: List[Dict[str, Any]],
    locations: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Generates fraud-linked multi-hop transactions, cashout events, account labels, and case relationships.

    Args:
        config: Generation configuration.
        complaints: Generated cybercrime complaints.
        accounts: Generated accounts pool.
        locations: Generated locations pool.

    Returns:
        Tuple containing:
        - fraud_transactions: List of fraud-linked transaction records
        - cashout_events: List of cashout event records
        - account_labels: List of account ground-truth labels (0 or 1)
        - case_relationships: List of inter-case graph relationships
    """
    rng = random.Random(config.seed + 300)
    location_ids = [loc["location_id"] for loc in locations] if locations else []

    # Map accounts by profile
    mule_candidates = [
        acc["account_id"] for acc in accounts
        if acc["synthetic_profile_type"] in ["synthetic_mule_candidate", "intermediary"]
    ]
    if not mule_candidates:
        mule_candidates = [acc["account_id"] for acc in accounts]

    all_account_ids = [acc["account_id"] for acc in accounts]
    account_lookup = {acc["account_id"]: acc for acc in accounts}

    # Identify dedicated shared syndicate hubs (12% of mule pool)
    num_shared_mules = max(3, int(len(mule_candidates) * 0.12))
    shared_mules = mule_candidates[:num_shared_mules]
    regular_mules = mule_candidates[num_shared_mules:] or mule_candidates

    transactions: List[Dict[str, Any]] = []
    cashouts: List[Dict[str, Any]] = []
    case_relationships: List[Dict[str, Any]] = []

    # Track role and behavior reason for each account
    account_label_map: Dict[str, Dict[str, Any]] = {}
    mule_accounts_set: Set[str] = set()

    # Track shared account participation in cases for Scenario 7 & 8
    account_cases_map: Dict[str, List[str]] = {}

    txn_counter = 1
    cashout_counter = 1
    rel_counter = 1

    # Scenario distributions:
    # 1. single_hop_rapid: Victim -> Mule 1 -> ATM (15%)
    # 2. two_hop_layering: Victim -> L1 Mule -> L2 Mule -> ATM (25%)
    # 3. deep_multihop: Victim -> L1 -> L2 -> L3 (-> L4) -> ATM (15%)
    # 4. fan_out_split: Victim -> L1 -> [L2A, L2B, L2C] -> ATMs (20%)
    # 5. multi_location_cashout: Terminal mule splits cashout across 2-3 ATMs (10%)
    # 6. shared_syndicate: Links to shared syndicate hubs (10%)
    # 7. digital_only_or_holding: No cashout (5%)
    scenario_choices = [
        "single_hop_rapid",
        "two_hop_layering",
        "deep_multihop",
        "fan_out_split",
        "multi_location_cashout",
        "shared_syndicate",
        "digital_only_or_holding",
    ]
    scenario_weights = [0.15, 0.25, 0.15, 0.20, 0.10, 0.10, 0.05]

    target_future_rate = config.future_cashout_rate  # ~0.42

    for comp in complaints:
        case_id = comp["case_id"]
        victim_id = comp["victim_account_id"]
        fraud_amt = float(comp["fraud_amount"])
        fraud_channel = comp["fraud_channel"]
        t_fraud = datetime.fromisoformat(comp["fraud_occurred_at"].replace("Z", "+00:00"))
        t_complaint = datetime.fromisoformat(comp["complaint_registered_at"].replace("Z", "+00:00"))
        delay_minutes = comp["complaint_delay_minutes"]
        event_group_id = f"GRP_{case_id}"

        scenario = rng.choices(scenario_choices, weights=scenario_weights, k=1)[0]

        # Determine whether this case will have a future cash-out event (after t_complaint)
        # Fresh & moderate complaints are primary candidates for future cash-out
        if scenario == "digital_only_or_holding":
            should_have_future_cashout = False
            has_any_cashout = False
        elif delay_minutes > 10080:  # > 7 days old: already withdrawn in past
            should_have_future_cashout = False
            has_any_cashout = True
        else:
            # For fresh/moderate/day delays, probabilistically decide future vs past cashout
            # Bias fresh complaints to have higher future cashout rate
            if delay_minutes < 120:
                p_future = min(0.85, target_future_rate * 1.8)
            elif delay_minutes < 720:
                p_future = target_future_rate * 0.9
            else:
                p_future = target_future_rate * 0.3
            should_have_future_cashout = (rng.random() < p_future)
            has_any_cashout = True

        # Select Layer 1 Mule
        if scenario == "shared_syndicate" and shared_mules:
            layer1_mule = rng.choice(shared_mules)
        else:
            layer1_mule = rng.choice(regular_mules)

        if layer1_mule == victim_id:
            layer1_mule = rng.choice([a for a in mule_candidates if a != victim_id] or regular_mules)

        mule_accounts_set.add(layer1_mule)
        account_cases_map.setdefault(layer1_mule, []).append(case_id)

        account_label_map[layer1_mule] = {
            "account_id": layer1_mule,
            "is_synthetic_mule": 1,
            "synthetic_behaviour_type": "mule_layer_1_aggregator",
            "label_generation_reason": "Primary recipient account acting as direct funnel and layer-1 aggregator",
        }

        # Step 1: Victim -> Layer 1 Mule
        t_initial = t_fraud
        t_initial_end = t_initial + timedelta(seconds=rng.randint(3, 25))
        txn_id_1 = f"TXN_{txn_counter:07d}"
        txn_counter += 1

        comp["initial_transaction_id"] = txn_id_1

        init_loc = account_lookup.get(layer1_mule, {}).get("home_location_id") or (rng.choice(location_ids) if location_ids else None)

        tx_initial = {
            "transaction_id": txn_id_1,
            "case_id": case_id,
            "from_account_id": victim_id,
            "to_account_id": layer1_mule,
            "amount": round_curr(fraud_amt),
            "currency": "INR",
            "transaction_type": "transfer",
            "channel": fraud_channel,
            "transaction_status": "completed",
            "initiated_at": t_initial.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "completed_at": t_initial_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "location_id": init_loc,
            "is_fraud_linked": True,
            "synthetic_event_group_id": event_group_id,
            "created_at": t_initial_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        transactions.append(tx_initial)

        t_current = t_initial_end

        # Helper to determine cashout timestamp
        def get_cashout_time(reference_time: datetime) -> datetime:
            if should_have_future_cashout:
                # Future cashout: occurs AFTER t_complaint
                mins_after_complaint = rng.randint(10, 180)
                return t_complaint + timedelta(minutes=mins_after_complaint)
            else:
                # Past cashout: occurs before t_complaint
                max_past_delay = max(5, int((t_complaint - reference_time).total_seconds() / 60) - 2)
                mins_past = rng.randint(4, min(max_past_delay, 120))
                return reference_time + timedelta(minutes=mins_past)

        # -------------------------------------------------------------
        # Scenario 1: Single-Hop Rapid Cash-Out
        # -------------------------------------------------------------
        if scenario == "single_hop_rapid":
            if has_any_cashout:
                t_cashout = get_cashout_time(t_current)
                cashout_amt = round_curr(fraud_amt * rng.uniform(0.92, 0.99))
                cashout_loc = account_lookup.get(layer1_mule, {}).get("home_location_id") or (rng.choice(location_ids) if location_ids else "SYNTH_LOC_0001")

                txn_id_c = f"TXN_{txn_counter:07d}"
                txn_counter += 1

                tx_cash = {
                    "transaction_id": txn_id_c,
                    "case_id": case_id,
                    "from_account_id": layer1_mule,
                    "to_account_id": "ACC_ATM_TERMINAL",
                    "amount": cashout_amt,
                    "currency": "INR",
                    "transaction_type": "withdrawal",
                    "channel": "ATM",
                    "transaction_status": "completed",
                    "initiated_at": t_cashout.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "completed_at": (t_cashout + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "location_id": cashout_loc,
                    "is_fraud_linked": True,
                    "synthetic_event_group_id": event_group_id,
                    "created_at": (t_cashout + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                transactions.append(tx_cash)

                csh_id = f"CSH_{cashout_counter:06d}"
                cashout_counter += 1
                is_future = t_cashout > t_complaint
                mins_since_prev = max(1, int((t_cashout - t_current).total_seconds() / 60))

                cashout_rec = {
                    "cashout_event_id": csh_id,
                    "case_id": case_id,
                    "account_id": layer1_mule,
                    "location_id": cashout_loc,
                    "transaction_id": txn_id_c,
                    "withdrawal_amount": cashout_amt,
                    "cashout_occurred_at": t_cashout.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "minutes_since_previous_transaction": mins_since_prev,
                    "is_future_ground_truth": is_future,
                    "synthetic_event_group_id": event_group_id,
                    "created_at": (t_cashout + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                cashouts.append(cashout_rec)

        # -------------------------------------------------------------
        # Scenario 2 & 6 & 8: Two-Hop Layering / Delayed Cash-Out
        # -------------------------------------------------------------
        elif scenario in ["two_hop_layering", "shared_syndicate"]:
            hop1_delay = rng.randint(3, 20)
            t_hop1 = t_current + timedelta(minutes=hop1_delay)

            layer2_candidates = [m for m in mule_candidates if m != layer1_mule and m != victim_id]
            if scenario == "shared_syndicate" and shared_mules:
                layer2_mule = rng.choice([m for m in shared_mules if m != layer1_mule] or layer2_candidates)
            else:
                layer2_mule = rng.choice(layer2_candidates) if layer2_candidates else regular_mules[0]

            mule_accounts_set.add(layer2_mule)
            account_cases_map.setdefault(layer2_mule, []).append(case_id)

            account_label_map[layer2_mule] = {
                "account_id": layer2_mule,
                "is_synthetic_mule": 1,
                "synthetic_behaviour_type": "mule_layer_2_distributor",
                "label_generation_reason": "Layer-2 intermediary mule receiving rapid transfers and forwarding to cashout",
            }

            hop1_amt = round_curr(fraud_amt * rng.uniform(0.95, 0.99))
            txn_id_2 = f"TXN_{txn_counter:07d}"
            txn_counter += 1

            tx_hop1 = {
                "transaction_id": txn_id_2,
                "case_id": case_id,
                "from_account_id": layer1_mule,
                "to_account_id": layer2_mule,
                "amount": hop1_amt,
                "currency": "INR",
                "transaction_type": "transfer",
                "channel": rng.choice(["IMPS", "UPI", "NEFT"]),
                "transaction_status": "completed",
                "initiated_at": t_hop1.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "completed_at": (t_hop1 + timedelta(seconds=rng.randint(5, 30))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "location_id": account_lookup.get(layer2_mule, {}).get("home_location_id"),
                "is_fraud_linked": True,
                "synthetic_event_group_id": event_group_id,
                "created_at": (t_hop1 + timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            transactions.append(tx_hop1)

            if has_any_cashout:
                t_cashout = get_cashout_time(t_hop1)
                cashout_amt = round_curr(hop1_amt * rng.uniform(0.93, 0.99))
                cashout_loc = account_lookup.get(layer2_mule, {}).get("home_location_id") or (rng.choice(location_ids) if location_ids else "SYNTH_LOC_0001")

                txn_id_c = f"TXN_{txn_counter:07d}"
                txn_counter += 1

                tx_cash = {
                    "transaction_id": txn_id_c,
                    "case_id": case_id,
                    "from_account_id": layer2_mule,
                    "to_account_id": "ACC_ATM_TERMINAL",
                    "amount": cashout_amt,
                    "currency": "INR",
                    "transaction_type": "withdrawal",
                    "channel": "ATM",
                    "transaction_status": "completed",
                    "initiated_at": t_cashout.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "completed_at": (t_cashout + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "location_id": cashout_loc,
                    "is_fraud_linked": True,
                    "synthetic_event_group_id": event_group_id,
                    "created_at": (t_cashout + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                transactions.append(tx_cash)

                csh_id = f"CSH_{cashout_counter:06d}"
                cashout_counter += 1
                is_future = t_cashout > t_complaint
                mins_since_prev = max(1, int((t_cashout - t_hop1).total_seconds() / 60))

                cashout_rec = {
                    "cashout_event_id": csh_id,
                    "case_id": case_id,
                    "account_id": layer2_mule,
                    "location_id": cashout_loc,
                    "transaction_id": txn_id_c,
                    "withdrawal_amount": cashout_amt,
                    "cashout_occurred_at": t_cashout.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "minutes_since_previous_transaction": mins_since_prev,
                    "is_future_ground_truth": is_future,
                    "synthetic_event_group_id": event_group_id,
                    "created_at": (t_cashout + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                cashouts.append(cashout_rec)

        # -------------------------------------------------------------
        # Scenario 3: Deep Multi-Hop Layering (3-Hop & 4-Hop)
        # -------------------------------------------------------------
        elif scenario == "deep_multihop":
            num_hops = rng.choice([3, 4])
            current_mule = layer1_mule
            current_amt = fraud_amt
            t_hop = t_current

            trail_mules = [current_mule]
            for h in range(2, num_hops + 1):
                hop_delay = rng.randint(3, 18)
                t_hop = t_hop + timedelta(minutes=hop_delay)

                candidates = [m for m in mule_candidates if m not in trail_mules and m != victim_id]
                next_mule = rng.choice(candidates) if candidates else rng.choice(regular_mules)
                trail_mules.append(next_mule)

                mule_accounts_set.add(next_mule)
                account_cases_map.setdefault(next_mule, []).append(case_id)

                beh_role = f"mule_layer_{h}_transit" if h < num_hops else "mule_cashout_terminal"
                account_label_map[next_mule] = {
                    "account_id": next_mule,
                    "is_synthetic_mule": 1,
                    "synthetic_behaviour_type": beh_role,
                    "label_generation_reason": f"Multi-hop layer-{h} transit node in deep laundering chain",
                }

                hop_amt = round_curr(current_amt * rng.uniform(0.96, 0.99))
                txn_id_hop = f"TXN_{txn_counter:07d}"
                txn_counter += 1

                tx_hop = {
                    "transaction_id": txn_id_hop,
                    "case_id": case_id,
                    "from_account_id": current_mule,
                    "to_account_id": next_mule,
                    "amount": hop_amt,
                    "currency": "INR",
                    "transaction_type": "transfer",
                    "channel": rng.choice(["IMPS", "UPI", "NEFT"]),
                    "transaction_status": "completed",
                    "initiated_at": t_hop.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "completed_at": (t_hop + timedelta(seconds=25)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "location_id": account_lookup.get(next_mule, {}).get("home_location_id"),
                    "is_fraud_linked": True,
                    "synthetic_event_group_id": event_group_id,
                    "created_at": (t_hop + timedelta(seconds=25)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                transactions.append(tx_hop)

                current_mule = next_mule
                current_amt = hop_amt

            if has_any_cashout:
                t_cashout = get_cashout_time(t_hop)
                cashout_amt = round_curr(current_amt * rng.uniform(0.92, 0.99))
                cashout_loc = account_lookup.get(current_mule, {}).get("home_location_id") or (rng.choice(location_ids) if location_ids else "SYNTH_LOC_0001")

                txn_id_c = f"TXN_{txn_counter:07d}"
                txn_counter += 1

                tx_cash = {
                    "transaction_id": txn_id_c,
                    "case_id": case_id,
                    "from_account_id": current_mule,
                    "to_account_id": "ACC_ATM_TERMINAL",
                    "amount": cashout_amt,
                    "currency": "INR",
                    "transaction_type": "withdrawal",
                    "channel": "ATM",
                    "transaction_status": "completed",
                    "initiated_at": t_cashout.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "completed_at": (t_cashout + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "location_id": cashout_loc,
                    "is_fraud_linked": True,
                    "synthetic_event_group_id": event_group_id,
                    "created_at": (t_cashout + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                transactions.append(tx_cash)

                csh_id = f"CSH_{cashout_counter:06d}"
                cashout_counter += 1
                is_future = t_cashout > t_complaint
                mins_since_prev = max(1, int((t_cashout - t_hop).total_seconds() / 60))

                cashout_rec = {
                    "cashout_event_id": csh_id,
                    "case_id": case_id,
                    "account_id": current_mule,
                    "location_id": cashout_loc,
                    "transaction_id": txn_id_c,
                    "withdrawal_amount": cashout_amt,
                    "cashout_occurred_at": t_cashout.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "minutes_since_previous_transaction": mins_since_prev,
                    "is_future_ground_truth": is_future,
                    "synthetic_event_group_id": event_group_id,
                    "created_at": (t_cashout + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                cashouts.append(cashout_rec)

        # -------------------------------------------------------------
        # Scenario 4: Fan-Out Split Transfers
        # -------------------------------------------------------------
        elif scenario == "fan_out_split":
            num_splits = rng.randint(2, 4)
            split_delay = rng.randint(3, 15)
            t_split = t_current + timedelta(minutes=split_delay)

            layer2_pool = [m for m in mule_candidates if m != layer1_mule and m != victim_id]
            selected_layer2 = rng.sample(layer2_pool, min(num_splits, len(layer2_pool)))

            total_forward = fraud_amt * 0.985
            split_fractions = [rng.uniform(0.7, 1.3) for _ in range(len(selected_layer2))]
            sum_f = sum(split_fractions)
            split_amounts = [round_curr(total_forward * (f / sum_f)) for f in split_fractions]

            for idx_sp, l2_acc in enumerate(selected_layer2):
                mule_accounts_set.add(l2_acc)
                account_cases_map.setdefault(l2_acc, []).append(case_id)

                account_label_map[l2_acc] = {
                    "account_id": l2_acc,
                    "is_synthetic_mule": 1,
                    "synthetic_behaviour_type": "mule_cashout_terminal",
                    "label_generation_reason": "Fan-out recipient terminal account performing localized cash withdrawal",
                }

                amt_sp = split_amounts[idx_sp]
                if amt_sp <= 0:
                    continue

                txn_id_sp = f"TXN_{txn_counter:07d}"
                txn_counter += 1

                tx_split = {
                    "transaction_id": txn_id_sp,
                    "case_id": case_id,
                    "from_account_id": layer1_mule,
                    "to_account_id": l2_acc,
                    "amount": amt_sp,
                    "currency": "INR",
                    "transaction_type": "transfer",
                    "channel": "UPI",
                    "transaction_status": "completed",
                    "initiated_at": t_split.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "completed_at": (t_split + timedelta(seconds=15)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "location_id": account_lookup.get(l2_acc, {}).get("home_location_id"),
                    "is_fraud_linked": True,
                    "synthetic_event_group_id": event_group_id,
                    "created_at": (t_split + timedelta(seconds=15)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                transactions.append(tx_split)

                if has_any_cashout and rng.random() < 0.85:
                    t_csh = get_cashout_time(t_split)
                    csh_amt = round_curr(amt_sp * rng.uniform(0.91, 0.98))
                    csh_loc = account_lookup.get(l2_acc, {}).get("home_location_id") or (rng.choice(location_ids) if location_ids else "SYNTH_LOC_0001")

                    txn_id_c = f"TXN_{txn_counter:07d}"
                    txn_counter += 1

                    tx_cash = {
                        "transaction_id": txn_id_c,
                        "case_id": case_id,
                        "from_account_id": l2_acc,
                        "to_account_id": "ACC_ATM_TERMINAL",
                        "amount": csh_amt,
                        "currency": "INR",
                        "transaction_type": "withdrawal",
                        "channel": "ATM",
                        "transaction_status": "completed",
                        "initiated_at": t_csh.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "completed_at": (t_csh + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "location_id": csh_loc,
                        "is_fraud_linked": True,
                        "synthetic_event_group_id": event_group_id,
                        "created_at": (t_csh + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                    transactions.append(tx_cash)

                    csh_id = f"CSH_{cashout_counter:06d}"
                    cashout_counter += 1
                    is_future = t_csh > t_complaint
                    mins_since_prev = max(1, int((t_csh - t_split).total_seconds() / 60))

                    cashout_rec = {
                        "cashout_event_id": csh_id,
                        "case_id": case_id,
                        "account_id": l2_acc,
                        "location_id": csh_loc,
                        "transaction_id": txn_id_c,
                        "withdrawal_amount": csh_amt,
                        "cashout_occurred_at": t_csh.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "minutes_since_previous_transaction": mins_since_prev,
                        "is_future_ground_truth": is_future,
                        "synthetic_event_group_id": event_group_id,
                        "created_at": (t_csh + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                    cashouts.append(cashout_rec)

        # -------------------------------------------------------------
        # Scenario 5: Multi-Location ATM Cash-Out (2-3 partial withdrawals)
        # -------------------------------------------------------------
        elif scenario == "multi_location_cashout":
            hop1_delay = rng.randint(4, 18)
            t_hop1 = t_current + timedelta(minutes=hop1_delay)

            layer2_candidates = [m for m in mule_candidates if m != layer1_mule and m != victim_id]
            terminal_mule = rng.choice(layer2_candidates) if layer2_candidates else regular_mules[0]

            mule_accounts_set.add(terminal_mule)
            account_cases_map.setdefault(terminal_mule, []).append(case_id)

            account_label_map[terminal_mule] = {
                "account_id": terminal_mule,
                "is_synthetic_mule": 1,
                "synthetic_behaviour_type": "mule_cashout_terminal",
                "label_generation_reason": "Terminal mule executing multi-ATM serial withdrawals",
            }

            hop1_amt = round_curr(fraud_amt * 0.985)
            txn_id_2 = f"TXN_{txn_counter:07d}"
            txn_counter += 1

            tx_hop1 = {
                "transaction_id": txn_id_2,
                "case_id": case_id,
                "from_account_id": layer1_mule,
                "to_account_id": terminal_mule,
                "amount": hop1_amt,
                "currency": "INR",
                "transaction_type": "transfer",
                "channel": "IMPS",
                "transaction_status": "completed",
                "initiated_at": t_hop1.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "completed_at": (t_hop1 + timedelta(seconds=20)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "location_id": account_lookup.get(terminal_mule, {}).get("home_location_id"),
                "is_fraud_linked": True,
                "synthetic_event_group_id": event_group_id,
                "created_at": (t_hop1 + timedelta(seconds=20)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            transactions.append(tx_hop1)

            if has_any_cashout:
                num_withdrawals = rng.choice([2, 3])
                base_csh_time = get_cashout_time(t_hop1)
                part_amt = round_curr(hop1_amt * 0.95 / num_withdrawals)

                nearby_locs = rng.sample(location_ids, min(num_withdrawals, len(location_ids))) if location_ids else ["SYNTH_LOC_0001"]

                for w_idx, w_loc in enumerate(nearby_locs):
                    t_w = base_csh_time + timedelta(minutes=w_idx * rng.randint(8, 25))
                    txn_id_c = f"TXN_{txn_counter:07d}"
                    txn_counter += 1

                    tx_cash = {
                        "transaction_id": txn_id_c,
                        "case_id": case_id,
                        "from_account_id": terminal_mule,
                        "to_account_id": "ACC_ATM_TERMINAL",
                        "amount": part_amt,
                        "currency": "INR",
                        "transaction_type": "withdrawal",
                        "channel": "ATM",
                        "transaction_status": "completed",
                        "initiated_at": t_w.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "completed_at": (t_w + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "location_id": w_loc,
                        "is_fraud_linked": True,
                        "synthetic_event_group_id": event_group_id,
                        "created_at": (t_w + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                    transactions.append(tx_cash)

                    csh_id = f"CSH_{cashout_counter:06d}"
                    cashout_counter += 1
                    is_future = t_w > t_complaint
                    mins_since_prev = max(1, int((t_w - t_hop1).total_seconds() / 60))

                    cashout_rec = {
                        "cashout_event_id": csh_id,
                        "case_id": case_id,
                        "account_id": terminal_mule,
                        "location_id": w_loc,
                        "transaction_id": txn_id_c,
                        "withdrawal_amount": part_amt,
                        "cashout_occurred_at": t_w.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "minutes_since_previous_transaction": mins_since_prev,
                        "is_future_ground_truth": is_future,
                        "synthetic_event_group_id": event_group_id,
                        "created_at": (t_w + timedelta(seconds=45)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                    cashouts.append(cashout_rec)

        # -------------------------------------------------------------
        # Scenario 7: Digital-Only Drain / Unwithdrawn Holding
        # -------------------------------------------------------------
        elif scenario == "digital_only_or_holding":
            # Either holds at Layer 1 or forwards to Layer 2 digital wallet/merchant
            if rng.random() < 0.65:
                hop1_delay = rng.randint(4, 25)
                t_hop1 = t_current + timedelta(minutes=hop1_delay)

                layer2_candidates = [m for m in mule_candidates if m != layer1_mule and m != victim_id]
                layer2_mule = rng.choice(layer2_candidates) if layer2_candidates else regular_mules[0]

                mule_accounts_set.add(layer2_mule)
                account_cases_map.setdefault(layer2_mule, []).append(case_id)

                account_label_map[layer2_mule] = {
                    "account_id": layer2_mule,
                    "is_synthetic_mule": 1,
                    "synthetic_behaviour_type": "mule_layer_2_distributor",
                    "label_generation_reason": "Digital intermediary holding or routing unwithdrawn cybercrime proceeds",
                }

                hop1_amt = round_curr(fraud_amt * 0.98)
                txn_id_2 = f"TXN_{txn_counter:07d}"
                txn_counter += 1

                tx_hop1 = {
                    "transaction_id": txn_id_2,
                    "case_id": case_id,
                    "from_account_id": layer1_mule,
                    "to_account_id": layer2_mule,
                    "amount": hop1_amt,
                    "currency": "INR",
                    "transaction_type": "transfer",
                    "channel": "wallet",
                    "transaction_status": "completed",
                    "initiated_at": t_hop1.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "completed_at": (t_hop1 + timedelta(seconds=15)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "location_id": account_lookup.get(layer2_mule, {}).get("home_location_id"),
                    "is_fraud_linked": True,
                    "synthetic_event_group_id": event_group_id,
                    "created_at": (t_hop1 + timedelta(seconds=15)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                transactions.append(tx_hop1)
            # No physical ATM cashouts generated

    # Ensure ACC_ATM_TERMINAL account exists in accounts
    if "ACC_ATM_TERMINAL" not in account_lookup:
        atm_account = {
            "account_id": "ACC_ATM_TERMINAL",
            "account_type": "intermediary",
            "account_opened_at": "2024-01-01T00:00:00Z",
            "account_age_days": 850,
            "home_location_id": location_ids[0] if location_ids else None,
            "account_status": "active",
            "baseline_transaction_count": 50000,
            "baseline_monthly_inflow": 50000000.0,
            "baseline_monthly_outflow": 50000000.0,
            "synthetic_profile_type": "intermediary",
            "created_at": "2024-01-01T00:00:00Z",
        }
        accounts.append(atm_account)
        account_lookup["ACC_ATM_TERMINAL"] = atm_account

    # Generate Case Relationships from shared accounts (Scenario 7)
    for acc_id, linked_cases in account_cases_map.items():
        if len(linked_cases) >= 2:
            unique_cases = list(dict.fromkeys(linked_cases))
            for i in range(len(unique_cases)):
                for j in range(i + 1, min(i + 5, len(unique_cases))):
                    rel_id = f"REL_{rel_counter:06d}"
                    rel_counter += 1
                    case_relationships.append({
                        "relationship_id": rel_id,
                        "case_id": unique_cases[i],
                        "related_case_id": unique_cases[j],
                        "account_id": acc_id,
                        "relationship_type": "shared_mule_account",
                        "shared_transaction_count": 2,
                        "shared_account_count": 1,
                        "relationship_created_at": config.base_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    })

    # Generate account labels for all accounts in the system
    account_labels: List[Dict[str, Any]] = []
    base_ts = config.base_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    for acc in accounts:
        acc_id = acc["account_id"]
        if acc_id == "ACC_ATM_TERMINAL":
            account_labels.append({
                "account_id": acc_id,
                "is_synthetic_mule": 0,
                "synthetic_behaviour_type": "atm_cash_dispenser_terminal",
                "label_generation_reason": "Synthetic bank ATM terminal account for physical cash settlement",
                "label_created_at": base_ts,
            })
            continue

        if acc_id in account_label_map:
            rec = account_label_map[acc_id]
            rec["label_created_at"] = base_ts
            account_labels.append(rec)
        else:
            profile = acc["synthetic_profile_type"]
            if profile == "high_volume":
                beh_type = "legitimate_merchant_high_vol"
                reason = "High-volume commercial merchant transactions with balanced inflow/outflow and established tenure"
            elif profile == "intermediary":
                beh_type = "legitimate_corporate_clearing"
                reason = "Authorized merchant aggregator/payroll routing clearing node"
            else:
                beh_type = "legitimate_individual"
                reason = "Standard retail customer with normal personal utility and payroll transfers"

            account_labels.append({
                "account_id": acc_id,
                "is_synthetic_mule": 0,
                "synthetic_behaviour_type": beh_type,
                "label_generation_reason": reason,
                "label_created_at": base_ts,
            })

    return transactions, cashouts, account_labels, case_relationships
