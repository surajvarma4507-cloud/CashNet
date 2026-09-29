"""CASHNET Synthetic Financial Data Generation & Ground Truth Engine CLI.

Smart India Hackathon - SIH26184 | AI-Powered Cybercrime Cash-Out Prediction & Intervention Platform
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

from .config import GenerationConfig
from .database_loader import load_into_database
from .export import export_all_datasets
from .generators.accounts import generate_accounts
from .generators.complaints import generate_complaints
from .generators.ground_truth import generate_ground_truth_and_snapshots
from .generators.locations import generate_locations
from .generators.networks import generate_transaction_networks
from .generators.transactions import generate_normal_transactions
from .validation import run_all_validations


def generate_all(config: GenerationConfig) -> Dict[str, List[Dict[str, Any]]]:
    """Generates the full interrelated CASHNET synthetic dataset world.

    Args:
        config: GenerationConfig instance.

    Returns:
        Dictionary mapping all table names to their generated records.
    """
    print(f"\n[*] Generating synthetic world (Profile: {config.profile.upper()}, Seed: {config.seed})...")

    # Step 1: Locations
    print(f"  [1/7] Generating Indian metropolitan locations ({config.num_locations} target)...")
    locations = generate_locations(config)

    # Step 2: Accounts
    print(f"  [2/7] Generating synthetic accounts and behavioral profiles ({config.num_accounts} target)...")
    accounts = generate_accounts(config, locations)

    # Step 3: Complaints
    print(f"  [3/7] Generating cybercrime complaints ({config.num_complaints} target)...")
    complaints = generate_complaints(config, accounts, locations)

    # Step 4: Networks, Fraud Money-Trails, Cashouts, Mule Labels, Relationships
    print("  [4/7] Constructing multi-hop fraud trails, split transfers & cashouts...")
    fraud_txs, cashouts, account_labels, relationships = generate_transaction_networks(
        config, complaints, accounts, locations
    )

    # Step 5: Normal background transactions
    print(f"  [5/7] Generating normal background transactions ({config.num_transactions} total target)...")
    normal_txs = generate_normal_transactions(
        config, accounts, locations, len(fraud_txs), config.num_transactions
    )
    all_transactions = fraud_txs + normal_txs

    # Step 6: Prediction snapshots, location candidates, case features, and hidden ground truth
    print("  [6/7] Computing point-in-time prediction snapshots, candidate ranking & hidden ground truth...")
    snapshots, candidates, case_features, ground_truth = generate_ground_truth_and_snapshots(
        config, complaints, accounts, locations, all_transactions, cashouts
    )

    datasets = {
        "locations": locations,
        "accounts": accounts,
        "complaints": complaints,
        "transactions": all_transactions,
        "cashout_events": cashouts,
        "account_labels": account_labels,
        "prediction_snapshots": snapshots,
        "location_candidates": candidates,
        "case_relationships": relationships,
        "case_features": case_features,
        "prediction_ground_truth": ground_truth,
    }

    print("  [7/7] Synthetic generation complete.")
    return datasets


def main() -> None:
    """CLI Entrypoint for CASHNET Synthetic Data Generation Engine."""
    parser = argparse.ArgumentParser(
        description="CASHNET Synthetic Financial Data Generation & Ground Truth Engine (SIH26184)"
    )
    parser.add_argument(
        "--profile",
        choices=["small", "standard", "large", "dev", "demo", "custom"],
        default="standard",
        help="Dataset profile (small, standard, large, dev, demo)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic reproducibility")
    parser.add_argument("--complaints", type=int, help="Number of complaints to generate")
    parser.add_argument("--accounts", type=int, help="Number of accounts to generate")
    parser.add_argument("--transactions", type=int, help="Total number of transactions to generate")
    parser.add_argument("--locations", type=int, help="Number of locations to generate")
    parser.add_argument("--data-dir", type=str, default="data_v2", help="Output data directory")
    parser.add_argument("--db-url", type=str, default="sqlite:///./cashnet_dev.db", help="Database connection URL")
    parser.add_argument("--validate", action="store_true", help="Run validation suite on generated data")
    parser.add_argument("--load-db", action="store_true", help="Load generated data into database")
    parser.add_argument("--overwrite", action="store_true", default=True, help="Overwrite existing data files")

    args = parser.parse_args()

    # Build config
    override_kwargs = {}
    if args.complaints:
        override_kwargs["num_complaints"] = args.complaints
    if args.accounts:
        override_kwargs["num_accounts"] = args.accounts
    if args.transactions:
        override_kwargs["num_transactions"] = args.transactions
    if args.locations:
        override_kwargs["num_locations"] = args.locations

    config = GenerationConfig.from_profile(
        profile_name=args.profile,
        seed=args.seed,
        data_dir=Path(args.data_dir),
        db_url=args.db_url,
        overwrite=args.overwrite,
        **override_kwargs
    )

    datasets = generate_all(config)
    print(f"\n[*] Exporting datasets to '{config.data_dir}'...")
    manifest = export_all_datasets(datasets, config)
    print(f"  [+] Manifest generated at '{config.data_dir}/manifests/dataset_manifest.json'")
    print(f"  [+] Quality report generated at '{config.data_dir}/manifests/data_quality_report.json'")

    # Always run validation
    print("\n[*] Running Automated Anti-Leakage & Relational Validation Suite...")
    report = run_all_validations(datasets)
    print(report.summary())

    if not report.is_valid:
        print("\n[!] Validation failed! Please inspect the error log above.", file=sys.stderr)
        sys.exit(1)

    # Optional Database Loading
    if args.load_db:
        print(f"\n[*] Loading datasets into database ({config.db_url})...")
        success = load_into_database(datasets, db_url=config.db_url)
        if success:
            print("  [+] Database schema created and records successfully loaded!")
        else:
            print("  [X] Database loading encountered an issue.")

    print("\n[OK] CASHNET Synthetic Financial Data Engine executed successfully!\n")


if __name__ == "__main__":
    main()
