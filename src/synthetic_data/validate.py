"""CASHNET Dataset Validation CLI.

Usage:
    python -m src.synthetic_data.validate --data-dir data_v2
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List

from .export import TABLE_EXPORT_PATHS
from .validation import run_all_validations


def load_datasets_from_csv(data_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Loads CSV files from the specified directory for validation."""
    datasets: Dict[str, List[Dict[str, Any]]] = {}
    for tbl, rel_path in TABLE_EXPORT_PATHS.items():
        file_path = data_dir / rel_path
        if not file_path.exists():
            print(f"  [!] Missing expected CSV file: {file_path}")
            continue

        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader)
            # Normalize empty strings to None for fields
            for r in records:
                for k, v in r.items():
                    if v == "":
                        r[k] = None
                    elif k in ["amount", "fraud_amount", "withdrawal_amount", "actual_cashout_amount",
                              "total_inflow_24h", "total_outflow_24h", "estimated_remaining_amount",
                              "nearest_location_distance_km", "distance_from_account_km",
                              "latitude", "longitude", "account_risk_score", "historical_location_risk",
                              "network_branching_factor", "total_cashout_amount", "average_transaction_amount",
                              "max_transaction_amount", "baseline_monthly_inflow", "baseline_monthly_outflow"]:
                        try:
                            r[k] = float(v)
                        except (ValueError, TypeError):
                            pass
                    elif k in ["complaint_delay_minutes", "minutes_since_last_transaction",
                              "incoming_transaction_count_1h", "outgoing_transaction_count_1h",
                              "incoming_transaction_count_24h", "outgoing_transaction_count_24h",
                              "unique_incoming_sources_24h", "linked_account_count", "linked_case_count",
                              "historical_cashout_count", "hour_of_day", "day_of_week",
                              "historical_case_count", "candidate_rank_reference", "shared_transaction_count",
                              "shared_account_count", "transaction_count", "unique_account_count",
                              "network_depth", "cashout_count", "distinct_cashout_locations",
                              "actual_minutes_until_cashout", "account_age_days", "baseline_transaction_count",
                              "is_synthetic_mule"]:
                        try:
                            r[k] = int(v)
                        except (ValueError, TypeError):
                            pass
                    elif k in ["has_future_cashout", "is_future_ground_truth", "is_fraud_linked", "is_active"]:
                        r[k] = (str(v).lower() in ["true", "1"])
            datasets[tbl] = records

    return datasets


def main() -> None:
    """CLI Entrypoint for CASHNET Synthetic Data Validation."""
    parser = argparse.ArgumentParser(
        description="CASHNET Synthetic Data Validation Engine (SIH26184)"
    )
    parser.add_argument("--data-dir", type=str, default="data_v2", help="Directory containing dataset CSVs")

    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    print(f"\n=======================================================")
    print(f" CASHNET Synthetic Data Validation Engine")
    print(f" Target Directory: {data_dir.resolve()}")
    print(f"=======================================================")

    if not data_dir.exists():
        print(f"[!] Target data directory '{data_dir}' does not exist!", file=sys.stderr)
        sys.exit(1)

    print("[*] Loading CSV tables into memory...")
    datasets = load_datasets_from_csv(data_dir)

    if len(datasets) < len(TABLE_EXPORT_PATHS):
        print(f"[!] Found {len(datasets)}/{len(TABLE_EXPORT_PATHS)} expected tables.", file=sys.stderr)

    print("[*] Running Relational, Temporal, Financial, and Anti-Leakage Validations...\n")
    report = run_all_validations(datasets)
    print(report.summary())

    if not report.is_valid:
        print("\n[!] Validation FAILED with errors!", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n[OK] All dataset integrity and anti-leakage checks PASSED successfully!\n")


if __name__ == "__main__":
    main()
