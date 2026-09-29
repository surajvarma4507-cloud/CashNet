"""Export and Manifest Generation Engine for CASHNET Synthetic Financial Datasets."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .config import GenerationConfig


TABLE_EXPORT_PATHS: Dict[str, str] = {
    # Raw Datasets
    "accounts": "raw/accounts.csv",
    "complaints": "raw/complaints.csv",
    "transactions": "raw/transactions.csv",
    "locations": "raw/locations.csv",
    "cashout_events": "raw/cashout_events.csv",
    "account_labels": "raw/account_labels.csv",
    "case_relationships": "raw/case_relationships.csv",

    # Processed Datasets (Model Inputs)
    "prediction_snapshots": "processed/prediction_snapshots.csv",
    "location_candidates": "processed/location_candidates.csv",
    "case_features": "processed/case_features.csv",

    # Evaluation Datasets (Hidden Ground Truth)
    "prediction_ground_truth": "evaluation/prediction_ground_truth.csv",
}

COLUMN_CLASSIFICATION: Dict[str, Dict[str, str]] = {
    "accounts": {
        "account_id": "Identifier / Primary Key",
        "account_type": "Safe prediction-time feature",
        "account_opened_at": "Safe prediction-time feature",
        "account_age_days": "Safe prediction-time feature",
        "home_location_id": "Safe prediction-time feature",
        "account_status": "Safe prediction-time feature",
        "baseline_transaction_count": "Safe prediction-time feature",
        "baseline_monthly_inflow": "Safe prediction-time feature",
        "baseline_monthly_outflow": "Safe prediction-time feature",
        "synthetic_profile_type": "Post-event or leakage-prone field (Generator Metadata only)",
        "created_at": "Metadata",
    },
    "complaints": {
        "case_id": "Identifier / Primary Key",
        "victim_account_id": "Identifier / Foreign Key",
        "fraud_type": "Safe prediction-time feature",
        "fraud_channel": "Safe prediction-time feature",
        "fraud_amount": "Safe prediction-time feature",
        "fraud_currency": "Metadata",
        "fraud_occurred_at": "Safe prediction-time feature",
        "complaint_registered_at": "Safe prediction-time feature (Snapshot Anchor)",
        "complaint_delay_minutes": "Safe prediction-time feature",
        "victim_location_id": "Safe prediction-time feature",
        "initial_transaction_id": "Identifier / Foreign Key",
        "complaint_status": "Safe prediction-time feature",
        "synthetic_description": "Safe prediction-time feature (NLP text)",
        "created_at": "Metadata",
    },
    "transactions": {
        "transaction_id": "Identifier / Primary Key",
        "case_id": "Identifier / Foreign Key (NULL for normal background)",
        "from_account_id": "Identifier / Foreign Key",
        "to_account_id": "Identifier / Foreign Key",
        "amount": "Safe prediction-time feature (when t <= snapshot_ts)",
        "currency": "Metadata",
        "transaction_type": "Safe prediction-time feature (when t <= snapshot_ts)",
        "channel": "Safe prediction-time feature (when t <= snapshot_ts)",
        "transaction_status": "Safe prediction-time feature (when t <= snapshot_ts)",
        "initiated_at": "Safe prediction-time feature (when t <= snapshot_ts)",
        "completed_at": "Safe prediction-time feature (when t <= snapshot_ts)",
        "location_id": "Safe prediction-time feature (when t <= snapshot_ts)",
        "is_fraud_linked": "Safe prediction-time feature (when t <= snapshot_ts)",
        "synthetic_event_group_id": "Metadata / Traceability",
        "created_at": "Metadata",
    },
    "locations": {
        "location_id": "Identifier / Primary Key",
        "location_name": "Safe prediction-time feature",
        "location_type": "Safe prediction-time feature",
        "city": "Safe prediction-time feature",
        "region": "Safe prediction-time feature",
        "latitude": "Safe prediction-time feature",
        "longitude": "Safe prediction-time feature",
        "area_cluster_id": "Safe prediction-time feature",
        "synthetic_location_group": "Safe prediction-time feature",
        "is_active": "Safe prediction-time feature",
        "created_at": "Metadata",
    },
    "cashout_events": {
        "cashout_event_id": "Identifier / Primary Key",
        "case_id": "Identifier / Foreign Key",
        "account_id": "Identifier / Foreign Key",
        "location_id": "Identifier / Foreign Key",
        "transaction_id": "Identifier / Foreign Key",
        "withdrawal_amount": "Post-event or leakage-prone field (Historical when t <= snapshot)",
        "cashout_occurred_at": "Post-event or leakage-prone field (Historical when t <= snapshot)",
        "minutes_since_previous_transaction": "Post-event or leakage-prone field",
        "is_future_ground_truth": "Target/ground-truth field (Evaluation only)",
        "synthetic_event_group_id": "Metadata / Traceability",
        "created_at": "Metadata",
    },
    "account_labels": {
        "account_id": "Identifier / Primary Key",
        "is_synthetic_mule": "Target/ground-truth field (Mule Risk Classifier Supervised Label)",
        "synthetic_behaviour_type": "Post-event or leakage-prone field (Audit / Evaluation only)",
        "label_generation_reason": "Metadata / Audit only",
        "label_created_at": "Metadata",
    },
    "prediction_snapshots": {
        "snapshot_id": "Identifier / Primary Key",
        "case_id": "Identifier / Foreign Key",
        "account_id": "Identifier / Foreign Key",
        "prediction_timestamp": "Safe prediction-time feature (Snapshot Anchor)",
        "complaint_delay_minutes": "Safe prediction-time feature",
        "minutes_since_last_transaction": "Safe prediction-time feature",
        "incoming_transaction_count_1h": "Safe prediction-time feature",
        "outgoing_transaction_count_1h": "Safe prediction-time feature",
        "incoming_transaction_count_24h": "Safe prediction-time feature",
        "outgoing_transaction_count_24h": "Safe prediction-time feature",
        "total_inflow_24h": "Safe prediction-time feature",
        "total_outflow_24h": "Safe prediction-time feature",
        "estimated_remaining_amount": "Safe prediction-time feature",
        "unique_incoming_sources_24h": "Safe prediction-time feature",
        "linked_account_count": "Safe prediction-time feature",
        "linked_case_count": "Safe prediction-time feature",
        "historical_cashout_count": "Safe prediction-time feature",
        "nearest_location_distance_km": "Safe prediction-time feature",
        "hour_of_day": "Safe prediction-time feature",
        "day_of_week": "Safe prediction-time feature",
        "account_risk_score": "Safe prediction-time feature",
        "prediction_mode": "Safe prediction-time feature (prediction / investigation)",
        "created_at": "Metadata",
    },
    "location_candidates": {
        "candidate_id": "Identifier / Primary Key",
        "snapshot_id": "Identifier / Foreign Key",
        "location_id": "Identifier / Foreign Key",
        "distance_from_account_km": "Safe prediction-time feature",
        "historical_cashout_count": "Safe prediction-time feature",
        "historical_case_count": "Safe prediction-time feature",
        "historical_location_risk": "Safe prediction-time feature",
        "candidate_rank_reference": "Safe prediction-time feature (Distance reference rank)",
        "created_at": "Metadata",
    },
    "case_relationships": {
        "relationship_id": "Identifier / Primary Key",
        "case_id": "Identifier / Foreign Key",
        "related_case_id": "Identifier / Foreign Key",
        "account_id": "Identifier / Foreign Key",
        "relationship_type": "Safe prediction-time feature (Graph relationship)",
        "shared_transaction_count": "Safe prediction-time feature",
        "shared_account_count": "Safe prediction-time feature",
        "relationship_created_at": "Metadata",
    },
    "case_features": {
        "case_id": "Identifier / Primary Key",
        "fraud_amount": "Safe prediction-time feature",
        "complaint_delay_minutes": "Safe prediction-time feature",
        "transaction_count": "Safe prediction-time feature (Point-in-time past count)",
        "unique_account_count": "Safe prediction-time feature (Point-in-time past count)",
        "network_depth": "Safe prediction-time feature (Point-in-time)",
        "network_branching_factor": "Safe prediction-time feature (Point-in-time)",
        "cashout_count": "Safe prediction-time feature (Point-in-time past count)",
        "total_cashout_amount": "Safe prediction-time feature (Point-in-time past sum)",
        "distinct_cashout_locations": "Safe prediction-time feature (Point-in-time past count)",
        "average_transaction_amount": "Safe prediction-time feature (Point-in-time)",
        "max_transaction_amount": "Safe prediction-time feature (Point-in-time)",
        "synthetic_pattern_type": "Post-event or leakage-prone field (Qualitative forensic archetype)",
        "created_at": "Metadata",
    },
    "prediction_ground_truth": {
        "ground_truth_id": "Identifier / Primary Key",
        "snapshot_id": "Identifier / Foreign Key",
        "actual_next_cashout_event_id": "Target/ground-truth field (Hidden Cashout Link)",
        "actual_next_location_id": "Target/ground-truth field (Location Prediction Target)",
        "actual_next_cashout_at": "Target/ground-truth field (Cashout Timing Target)",
        "actual_minutes_until_cashout": "Target/ground-truth field (Time-Window Target Delta)",
        "actual_cashout_amount": "Target/ground-truth field (Withdrawal Amount Target)",
        "has_future_cashout": "Target/ground-truth field (Binary Occurrence Label)",
        "evaluation_status": "Target/ground-truth field (Evaluation Status)",
    },
}


def calculate_sha256(file_path: Path) -> str:
    """Calculates SHA256 hash of a file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def export_all_datasets(
    datasets: Dict[str, List[Dict[str, Any]]],
    config: GenerationConfig,
) -> Dict[str, Any]:
    """Exports all dataset tables to designated CSV files and writes dataset_manifest.json and quality reports.

    Args:
        datasets: Dictionary of table names to records list.
        config: Generation configuration.

    Returns:
        Manifest dictionary.
    """
    base_dir = config.data_dir
    base_dir.mkdir(parents=True, exist_ok=True)

    manifest_tables: Dict[str, Any] = {}

    for table_name, rel_path in TABLE_EXPORT_PATHS.items():
        records = datasets.get(table_name, [])
        file_path = base_dir / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if not records:
            continue

        fieldnames = list(records[0].keys())

        # Write UTF-8 CSV with stable column order
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in records:
                formatted_row = {
                    k: ("" if v is None else v)
                    for k, v in row.items()
                }
                writer.writerow(formatted_row)

        file_hash = calculate_sha256(file_path)
        manifest_tables[table_name] = {
            "relative_path": rel_path,
            "row_count": len(records),
            "column_count": len(fieldnames),
            "columns": fieldnames,
            "sha256_checksum": file_hash,
            "file_size_bytes": file_path.stat().st_size,
        }

    # Write Manifest
    manifest = {
        "generator_name": "CASHNET Synthetic Financial Data Engine",
        "generator_version": "2.0.0",
        "schema_version": "2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "random_seed": config.seed,
        "profile": config.profile,
        "base_currency": config.currency,
        "geographic_context": "India Metros (MMR, NCR, Bengaluru, Hyderabad, Kolkata, Pune, Chennai, Ahmedabad, Jaipur, Lucknow, Chandigarh, Kochi, Indore)",
        "synthetic_data_declaration": (
            "This dataset contains purely synthetic financial and cybercrime transaction intelligence "
            "generated for Smart India Hackathon problem statement SIH26184. No actual bank records, "
            "KYC, PII, Aadhaar, or confidential intelligence are contained herein."
        ),
        "table_manifest": manifest_tables,
    }

    manifest_path = base_dir / "manifests" / "dataset_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Write Feature Classification Manifest
    feature_manifest_path = base_dir / "manifests" / "feature_manifest.json"
    with open(feature_manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "feature_manifest_version": "2.0",
            "description": "Comprehensive classification of all dataset columns for anti-leakage governance",
            "tables": COLUMN_CLASSIFICATION,
        }, f, indent=2)

    # Calculate Data Quality Metrics
    snapshots = datasets.get("prediction_snapshots", [])
    ground_truth = datasets.get("prediction_ground_truth", [])
    complaints = datasets.get("complaints", [])
    accounts = datasets.get("account_labels", [])

    total_snaps = len(snapshots)
    pred_mode_snaps = sum(1 for s in snapshots if s.get("prediction_mode") == "prediction")
    inv_mode_snaps = sum(1 for s in snapshots if s.get("prediction_mode") == "investigation")

    positive_future_snaps = sum(1 for gt in ground_truth if gt.get("has_future_cashout"))
    no_future_snaps = total_snaps - positive_future_snaps

    status_counts = {}
    for gt in ground_truth:
        st = gt.get("evaluation_status", "unknown")
        status_counts[st] = status_counts.get(st, 0) + 1

    fraud_type_counts = {}
    for c in complaints:
        ft = c.get("fraud_type", "unknown")
        fraud_type_counts[ft] = fraud_type_counts.get(ft, 0) + 1

    mule_count = sum(1 for a in accounts if a.get("is_synthetic_mule") == 1)
    legit_count = sum(1 for a in accounts if a.get("is_synthetic_mule") == 0)

    quality_report = {
        "dataset_profile": config.profile,
        "seed": config.seed,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_complaints": len(complaints),
        "total_snapshots": total_snaps,
        "prediction_mode_snapshots": pred_mode_snaps,
        "investigation_mode_snapshots": inv_mode_snaps,
        "positive_future_cashout_snapshots": positive_future_snaps,
        "positive_future_cashout_pct_of_prediction_mode": round((positive_future_snaps / max(1, pred_mode_snaps)) * 100, 2),
        "no_future_cashout_snapshots": no_future_snaps,
        "evaluation_status_distribution": status_counts,
        "fraud_scenario_distribution": fraud_type_counts,
        "account_label_distribution": {
            "synthetic_mules": mule_count,
            "legitimate_accounts": legit_count,
            "mule_ratio": round(mule_count / max(1, len(accounts)), 4),
        },
        "total_transactions": len(datasets.get("transactions", [])),
        "total_cashouts": len(datasets.get("cashout_events", [])),
        "total_locations": len(datasets.get("locations", [])),
        "total_location_candidates": len(datasets.get("location_candidates", [])),
        "candidates_per_snapshot_avg": round(len(datasets.get("location_candidates", [])) / max(1, total_snaps), 2),
    }

    quality_report_path = base_dir / "manifests" / "data_quality_report.json"
    with open(quality_report_path, "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2)

    return manifest
