"""Complaints Generator for CASHNET Synthetic Financial Engine.

Generates realistic cybercrime complaints in Indian context (UPI fraud, phishing APKs,
Telegram task investment scams, AnyDesk remote fraud, Digital Arrest, and instant loan scams)
with realistic temporal reporting delays.
"""

import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from ..config import (
    COMPLAINT_STATUSES,
    COMPLAINT_TEMPLATES,
    FRAUD_TYPES,
    PAYMENT_CHANNELS,
    GenerationConfig,
)


def generate_complaints(
    config: GenerationConfig,
    accounts: List[Dict[str, Any]],
    locations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generates synthetic cybercrime complaints with realistic victim links and delays.

    Args:
        config: Generation configuration.
        accounts: Available accounts to choose victims from (prefers normal individuals/businesses).
        locations: Available locations.

    Returns:
        List of complaint dictionary records.
    """
    rng = random.Random(config.seed + 200)
    num_complaints = config.num_complaints

    # Eligible victims: normal or business accounts
    victim_candidates = [
        acc for acc in accounts
        if acc["synthetic_profile_type"] in ["normal", "high_volume"]
    ]
    if not victim_candidates:
        victim_candidates = accounts

    location_ids = [loc["location_id"] for loc in locations] if locations else []

    base_dt = config.base_date
    horizon_days = config.time_horizon_days

    complaints: List[Dict[str, Any]] = []

    for i in range(num_complaints):
        case_idx = i + 1
        case_id = f"CASE_2026_{case_idx:06d}"

        victim = rng.choice(victim_candidates)
        victim_account_id = victim["account_id"]
        victim_location_id = victim["home_location_id"] or (rng.choice(location_ids) if location_ids else None)

        fraud_type = rng.choice(FRAUD_TYPES)

        # Realistic fraud channel and amount distribution in INR
        if fraud_type == "upi_fraud":
            fraud_channel = rng.choices(["UPI", "wallet", "IMPS"], weights=[0.85, 0.10, 0.05], k=1)[0]
            amount = round(rng.uniform(3000.0, 99000.0), 2)
        elif fraud_type == "phishing":
            fraud_channel = rng.choices(["UPI", "IMPS", "NEFT", "card"], weights=[0.45, 0.35, 0.10, 0.10], k=1)[0]
            amount = round(rng.uniform(10000.0, 350000.0), 2)
        elif fraud_type == "social_engineering":
            fraud_channel = rng.choices(["UPI", "IMPS", "NEFT", "wallet"], weights=[0.50, 0.30, 0.15, 0.05], k=1)[0]
            amount = round(rng.uniform(15000.0, 500000.0), 2)
        elif fraud_type == "investment_scam":
            fraud_channel = rng.choices(["IMPS", "NEFT", "RTGS", "UPI"], weights=[0.40, 0.35, 0.15, 0.10], k=1)[0]
            amount = round(rng.uniform(50000.0, 3500000.0), 2)
        elif fraud_type == "remote_access_scam":
            fraud_channel = rng.choices(["IMPS", "NEFT", "UPI"], weights=[0.55, 0.30, 0.15], k=1)[0]
            amount = round(rng.uniform(25000.0, 850000.0), 2)
        elif fraud_type == "account_takeover":
            fraud_channel = rng.choices(["IMPS", "NEFT", "RTGS"], weights=[0.40, 0.35, 0.25], k=1)[0]
            amount = round(rng.uniform(100000.0, 4000000.0), 2)
        elif fraud_type == "digital_arrest_scam":
            fraud_channel = rng.choices(["RTGS", "NEFT", "IMPS"], weights=[0.45, 0.40, 0.15], k=1)[0]
            amount = round(rng.uniform(200000.0, 5000000.0), 2)
        else:  # loan_app_extortion
            fraud_channel = rng.choices(["UPI", "IMPS", "wallet"], weights=[0.70, 0.20, 0.10], k=1)[0]
            amount = round(rng.uniform(5000.0, 150000.0), 2)

        # Fraud occurrence time within simulation window
        # Buffer of 6 days at the end so cashouts and complaints can resolve
        day_offset = rng.randint(1, max(2, horizon_days - 7))
        hour_offset = rng.randint(0, 23)
        min_offset = rng.randint(0, 59)
        sec_offset = rng.randint(0, 59)

        fraud_occurred_at = base_dt + timedelta(
            days=day_offset,
            hours=hour_offset,
            minutes=min_offset,
            seconds=sec_offset
        )

        # Categorize complaint delay:
        # Fresh: < 2 hours (35%) -> Great for tactical intervention / prediction
        # Moderate: 2 - 12 hours (25%) -> Mix of active and completed
        # Day: 12 - 24 hours (15%) -> Mostly completed / layered
        # Old: 1 - 7 days (18%) -> Investigation mode
        # Very old: > 7 days (7%) -> Investigation mode
        delay_category = rng.choices(
            ["fresh", "moderate", "day", "old", "very_old"],
            weights=[0.35, 0.25, 0.15, 0.18, 0.07],
            k=1
        )[0]

        if delay_category == "fresh":
            delay_minutes = rng.randint(15, 115)
        elif delay_category == "moderate":
            delay_minutes = rng.randint(120, 720)
        elif delay_category == "day":
            delay_minutes = rng.randint(721, 1439)
        elif delay_category == "old":
            delay_minutes = rng.randint(1440, 10079)
        else:  # very_old
            delay_minutes = rng.randint(10080, 28800)

        complaint_registered_at = fraud_occurred_at + timedelta(minutes=delay_minutes)

        # Narrative description
        templates = COMPLAINT_TEMPLATES.get(fraud_type, ["Fraud incident involving INR {amount}."])
        template = rng.choice(templates)
        description = template.format(amount=f"{amount:,.2f}")

        # Complaint status
        status = rng.choices(
            COMPLAINT_STATUSES,
            weights=[0.50, 0.35, 0.10, 0.05],
            k=1
        )[0]

        record = {
            "case_id": case_id,
            "victim_account_id": victim_account_id,
            "fraud_type": fraud_type,
            "fraud_channel": fraud_channel,
            "fraud_amount": amount,
            "fraud_currency": "INR",
            "fraud_occurred_at": fraud_occurred_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "complaint_registered_at": complaint_registered_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "complaint_delay_minutes": delay_minutes,
            "victim_location_id": victim_location_id,
            "initial_transaction_id": None,  # Linked during network generation
            "complaint_status": status,
            "synthetic_description": description,
            "created_at": complaint_registered_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        complaints.append(record)

    return complaints
