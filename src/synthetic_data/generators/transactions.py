"""Transaction Generator for CASHNET Synthetic Financial Engine.

Generates normal background transactions (everyday peer-to-peer, salary, utility,
merchant transactions, routine ATM cash withdrawals, high-volume merchant flows,
and unusual non-criminal false-positive-like transactions).
"""

import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List

from ..config import PAYMENT_CHANNELS, GenerationConfig


def round_curr(val: float) -> float:
    """Rounds financial amount to 2 decimal places."""
    d = Decimal(str(val))
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def generate_normal_transactions(
    config: GenerationConfig,
    accounts: List[Dict[str, Any]],
    locations: List[Dict[str, Any]],
    existing_transactions_count: int,
    target_total_transactions: int,
) -> List[Dict[str, Any]]:
    """Generates normal background transactions to reach the target total transaction count.

    Args:
        config: Generation configuration.
        accounts: Available accounts.
        locations: Available locations.
        existing_transactions_count: Number of fraud-linked transactions already generated.
        target_total_transactions: Target total transaction count.

    Returns:
        List of normal background transaction records.
    """
    rng = random.Random(config.seed + 400)
    needed = max(0, target_total_transactions - existing_transactions_count)

    if needed == 0:
        return []

    # Filter out terminal account from regular account pool
    normal_accounts = [
        acc for acc in accounts
        if acc["account_id"] != "ACC_ATM_TERMINAL"
    ]
    if len(normal_accounts) < 2:
        return []

    high_vol_accounts = [
        acc for acc in normal_accounts
        if acc["synthetic_profile_type"] == "high_volume"
    ]
    regular_accounts = [
        acc for acc in normal_accounts
        if acc["synthetic_profile_type"] != "high_volume"
    ]

    location_ids = [loc["location_id"] for loc in locations] if locations else []
    account_lookup = {acc["account_id"]: acc for acc in normal_accounts}

    base_dt = config.base_date
    horizon_days = config.time_horizon_days

    transactions: List[Dict[str, Any]] = []
    start_counter = existing_transactions_count + 1

    # Batch generate transactions
    for i in range(needed):
        txn_idx = start_counter + i
        txn_id = f"TXN_{txn_idx:07d}"

        # Transaction category:
        # - High volume merchant: 25%
        # - Standard retail / P2P: 50%
        # - Unusual non-criminal / false-positive-like: 15%
        # - Routine ATM cash withdrawal: 10%
        cat = rng.choices(
            ["high_vol", "standard_retail", "false_positive_like", "routine_atm"],
            weights=[0.25, 0.50, 0.15, 0.10],
            k=1
        )[0]

        if cat == "high_vol" and high_vol_accounts:
            merchant = rng.choice(high_vol_accounts)
            buyer = rng.choice(regular_accounts or normal_accounts)
            while buyer["account_id"] == merchant["account_id"]:
                buyer = rng.choice(normal_accounts)

            # 80% buyer paying merchant, 20% merchant vendor payout
            if rng.random() < 0.80:
                from_acc, to_acc = buyer["account_id"], merchant["account_id"]
                channel = rng.choices(["UPI", "card", "wallet", "IMPS"], weights=[0.65, 0.15, 0.10, 0.10], k=1)[0]
                amount = round_curr(rng.uniform(150.0, 25000.0))
            else:
                from_acc, to_acc = merchant["account_id"], buyer["account_id"]
                channel = rng.choices(["IMPS", "NEFT", "RTGS"], weights=[0.45, 0.35, 0.20], k=1)[0]
                amount = round_curr(rng.uniform(25000.0, 450000.0))
            tx_type = "transfer"

        elif cat == "false_positive_like":
            # Legitimate unusual patterns (e.g. rent pool, event crowdfunding, wedding expenses)
            acc1 = rng.choice(normal_accounts)
            acc2 = rng.choice(normal_accounts)
            while acc2["account_id"] == acc1["account_id"]:
                acc2 = rng.choice(normal_accounts)

            fp_pattern = rng.choice(["large_lump_sum", "quick_round_trip", "salary_batch"])
            if fp_pattern == "large_lump_sum":
                from_acc, to_acc = acc1["account_id"], acc2["account_id"]
                channel = rng.choice(["NEFT", "RTGS", "IMPS"])
                amount = round_curr(rng.uniform(75000.0, 800000.0))
            elif fp_pattern == "quick_round_trip":
                from_acc, to_acc = acc1["account_id"], acc2["account_id"]
                channel = "UPI"
                amount = round_curr(rng.uniform(2000.0, 25000.0))
            else:
                from_acc, to_acc = acc1["account_id"], acc2["account_id"]
                channel = rng.choice(["IMPS", "NEFT"])
                amount = round_curr(rng.uniform(15000.0, 65000.0))
            tx_type = "transfer"

        elif cat == "routine_atm":
            # Normal individual cash withdrawal
            acc = rng.choice(normal_accounts)
            from_acc = acc["account_id"]
            to_acc = "ACC_ATM_TERMINAL"
            channel = "ATM"
            tx_type = "withdrawal"
            amount = round_curr(rng.choice([500.0, 1000.0, 2000.0, 2500.0, 4000.0, 5000.0, 8000.0, 10000.0]))

        else:  # standard_retail
            acc1 = rng.choice(normal_accounts)
            acc2 = rng.choice(normal_accounts)
            while acc2["account_id"] == acc1["account_id"]:
                acc2 = rng.choice(normal_accounts)

            from_acc, to_acc = acc1["account_id"], acc2["account_id"]
            channel = rng.choices(
                ["UPI", "IMPS", "NEFT", "wallet", "card"],
                weights=[0.68, 0.18, 0.06, 0.05, 0.03],
                k=1
            )[0]
            amount = round_curr(rng.uniform(50.0, 45000.0))
            tx_type = "transfer"

        # Timing distribution across simulation horizon
        day_offset = rng.randint(0, max(1, horizon_days - 1))
        hour_offset = rng.randint(0, 23)
        min_offset = rng.randint(0, 59)
        sec_offset = rng.randint(0, 59)

        t_init = base_dt + timedelta(
            days=day_offset,
            hours=hour_offset,
            minutes=min_offset,
            seconds=sec_offset
        )
        duration_secs = rng.randint(2, 35) if channel in ["UPI", "IMPS", "wallet", "ATM", "card"] else rng.randint(120, 3600)
        t_comp = t_init + timedelta(seconds=duration_secs)

        loc_id = account_lookup.get(from_acc, {}).get("home_location_id") or (rng.choice(location_ids) if location_ids else None)

        status = rng.choices(
            ["completed", "failed", "pending"],
            weights=[0.96, 0.03, 0.01],
            k=1
        )[0]

        grp_id = f"GRP_NORMAL_{i // 50:04d}"

        record = {
            "transaction_id": txn_id,
            "case_id": None,
            "from_account_id": from_acc,
            "to_account_id": to_acc,
            "amount": amount,
            "currency": "INR",
            "transaction_type": tx_type,
            "channel": channel,
            "transaction_status": status,
            "initiated_at": t_init.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "completed_at": t_comp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "location_id": loc_id,
            "is_fraud_linked": False,
            "synthetic_event_group_id": grp_id,
            "created_at": t_comp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        transactions.append(record)

    return transactions
