"""Account Generator for CASHNET Synthetic Financial Engine.

Generates realistic synthetic Indian accounts (Individual savings, Current business,
Wallets, Intermediaries) with diverse behavioural profiles, baseline volumes, and
unusual non-criminal / false-positive activity patterns.
"""

import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from ..config import ACCOUNT_STATUSES, ACCOUNT_TYPES, SYNTHETIC_PROFILE_TYPES, GenerationConfig


def generate_accounts(
    config: GenerationConfig,
    locations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generates synthetic accounts with realistic profiles and baseline stats.

    Ensures target labels are NOT trivially identifiable by account prefix or type.

    Args:
        config: Generation configuration.
        locations: Generated location records for home_location_id assignment.

    Returns:
        List of account dictionary records.
    """
    rng = random.Random(config.seed + 100)
    num_accounts = config.num_accounts
    location_ids = [loc["location_id"] for loc in locations] if locations else []

    accounts: List[Dict[str, Any]] = []

    # Calculate target counts for profiles
    mule_ratio = config.suspicious_account_ratio
    num_mule = max(1, int(num_accounts * mule_ratio))
    num_high_vol = max(1, int(num_accounts * 0.10))      # 10% legitimate high-volume merchants
    num_intermediary = max(1, int(num_accounts * 0.06))  # 6% legitimate corporate/payroll clearing nodes
    num_normal = num_accounts - (num_mule + num_high_vol + num_intermediary)

    profile_assignments = (
        ["synthetic_mule_candidate"] * num_mule +
        ["high_volume"] * num_high_vol +
        ["intermediary"] * num_intermediary +
        ["normal"] * num_normal
    )
    rng.shuffle(profile_assignments)

    base_dt = config.base_date

    for i in range(num_accounts):
        acc_idx = i + 1
        profile = profile_assignments[i]

        # Determine account type ensuring overlapping distributions across all profiles
        # (This prevents target label leakage from account type or prefix)
        if profile == "high_volume":
            acc_type = rng.choices(["business", "individual", "intermediary"], weights=[0.80, 0.12, 0.08], k=1)[0]
        elif profile == "intermediary":
            acc_type = rng.choices(["intermediary", "business", "wallet", "individual"], weights=[0.50, 0.25, 0.15, 0.10], k=1)[0]
        elif profile == "synthetic_mule_candidate":
            # Mules mimic real-world distribution across savings, wallets, current accounts, and fake shell intermediaries
            acc_type = rng.choices(["individual", "wallet", "business", "intermediary"], weights=[0.60, 0.22, 0.12, 0.06], k=1)[0]
        else:  # normal
            acc_type = rng.choices(["individual", "business", "wallet", "intermediary"], weights=[0.75, 0.15, 0.08, 0.02], k=1)[0]

        # Generate prefix strictly based on functional account_type (neutral to mule label)
        prefix = {
            "individual": "ACC_IND",
            "business": "ACC_BUS",
            "wallet": "ACC_WAL",
            "intermediary": "ACC_INT",
        }.get(acc_type, "ACC")
        acc_id = f"{prefix}_{acc_idx:06d}"

        # Account age and opened timestamp
        if profile == "synthetic_mule_candidate":
            # Realistic mule accounts: 65% new (10-180 days), 25% seasoned (180-720 days), 10% re-activated old dormant (720-2500 days)
            age_bucket = rng.choices(["new", "seasoned", "old_dormant"], weights=[0.65, 0.25, 0.10], k=1)[0]
            if age_bucket == "new":
                age_days = rng.randint(10, 180)
            elif age_bucket == "seasoned":
                age_days = rng.randint(181, 720)
            else:
                age_days = rng.randint(721, 2500)
        elif profile == "high_volume":
            age_days = rng.randint(180, 3650)
        else:
            age_days = rng.randint(30, 3650)

        opened_dt = base_dt - timedelta(days=age_days, hours=rng.randint(0, 23), minutes=rng.randint(0, 59))

        # Operational status
        if profile == "synthetic_mule_candidate":
            status = rng.choices(ACCOUNT_STATUSES, weights=[0.88, 0.06, 0.04, 0.02], k=1)[0]
        else:
            status = rng.choices(ACCOUNT_STATUSES, weights=[0.94, 0.03, 0.02, 0.01], k=1)[0]

        # Home location
        home_loc = rng.choice(location_ids) if location_ids and rng.random() < 0.96 else None

        # Baseline metrics (in INR)
        if profile == "high_volume":
            baseline_count = rng.randint(150, 1200)
            baseline_inflow = round(rng.uniform(600000.0, 12000000.0), 2)
            baseline_outflow = round(baseline_inflow * rng.uniform(0.90, 1.04), 2)
        elif profile == "intermediary":
            baseline_count = rng.randint(50, 350)
            baseline_inflow = round(rng.uniform(200000.0, 2500000.0), 2)
            baseline_outflow = round(baseline_inflow * rng.uniform(0.95, 1.02), 2)
        elif profile == "synthetic_mule_candidate":
            # Realistic baseline prior to fraud activation: varied across low, medium, or erratic
            baseline_type = rng.choices(["low", "moderate", "dormant_burst"], weights=[0.60, 0.30, 0.10], k=1)[0]
            if baseline_type == "low":
                baseline_count = rng.randint(2, 20)
                baseline_inflow = round(rng.uniform(3000.0, 40000.0), 2)
            elif baseline_type == "moderate":
                baseline_count = rng.randint(15, 60)
                baseline_inflow = round(rng.uniform(40000.0, 180000.0), 2)
            else:
                baseline_count = rng.randint(1, 8)
                baseline_inflow = round(rng.uniform(500.0, 15000.0), 2)
            baseline_outflow = round(baseline_inflow * rng.uniform(0.80, 1.15), 2)
        else:  # normal
            if acc_type == "business":
                baseline_count = rng.randint(40, 250)
                baseline_inflow = round(rng.uniform(120000.0, 1500000.0), 2)
                baseline_outflow = round(baseline_inflow * rng.uniform(0.82, 0.99), 2)
            elif acc_type == "wallet":
                baseline_count = rng.randint(10, 80)
                baseline_inflow = round(rng.uniform(2500.0, 50000.0), 2)
                baseline_outflow = round(baseline_inflow * rng.uniform(0.75, 0.99), 2)
            elif acc_type == "intermediary":
                baseline_count = rng.randint(30, 120)
                baseline_inflow = round(rng.uniform(100000.0, 900000.0), 2)
                baseline_outflow = round(baseline_inflow * rng.uniform(0.90, 1.01), 2)
            else:  # individual
                # Retail individuals: salary class, students, professionals
                tier = rng.choices(["entry", "mid", "affluent"], weights=[0.50, 0.40, 0.10], k=1)[0]
                if tier == "entry":
                    baseline_count = rng.randint(5, 30)
                    baseline_inflow = round(rng.uniform(12000.0, 60000.0), 2)
                elif tier == "mid":
                    baseline_count = rng.randint(15, 60)
                    baseline_inflow = round(rng.uniform(60000.0, 250000.0), 2)
                else:
                    baseline_count = rng.randint(25, 100)
                    baseline_inflow = round(rng.uniform(250000.0, 950000.0), 2)
                baseline_outflow = round(baseline_inflow * rng.uniform(0.60, 0.95), 2)

        record = {
            "account_id": acc_id,
            "account_type": acc_type,
            "account_opened_at": opened_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "account_age_days": age_days,
            "home_location_id": home_loc,
            "account_status": status,
            "baseline_transaction_count": baseline_count,
            "baseline_monthly_inflow": baseline_inflow,
            "baseline_monthly_outflow": baseline_outflow,
            "synthetic_profile_type": profile,
            "created_at": base_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        accounts.append(record)

    return accounts
