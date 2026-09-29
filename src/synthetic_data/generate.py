"""CASHNET Synthetic Financial Data Generator CLI.

Usage:
    python -m src.synthetic_data.generate --profile small --seed 42 --data-dir data_v2
    python -m src.synthetic_data.generate --profile standard --seed 42 --data-dir data_v2
    python -m src.synthetic_data.generate --profile large --seed 42 --data-dir data_v2
"""

import argparse
import sys
from pathlib import Path

from .config import GenerationConfig
from .database_loader import load_into_database
from .export import export_all_datasets
from .main import generate_all
from .validation import run_all_validations


def main() -> None:
    """CLI Entrypoint for CASHNET Synthetic Data Generation."""
    parser = argparse.ArgumentParser(
        description="CASHNET Synthetic Financial Data Generator (SIH26184)"
    )
    parser.add_argument(
        "--profile",
        choices=["small", "standard", "large", "dev", "demo", "custom"],
        default="standard",
        help="Dataset profile (small, standard, large)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic reproducibility")
    parser.add_argument("--complaints", type=int, help="Number of complaints to generate")
    parser.add_argument("--accounts", type=int, help="Number of accounts to generate")
    parser.add_argument("--transactions", type=int, help="Total number of transactions to generate")
    parser.add_argument("--locations", type=int, help="Number of locations to generate")
    parser.add_argument("--data-dir", type=str, default="data_v2", help="Output data directory")
    parser.add_argument("--db-url", type=str, default="sqlite:///./cashnet_dev.db", help="Database connection URL")
    parser.add_argument("--load-db", action="store_true", help="Load generated data into database")
    parser.add_argument("--skip-validation", action="store_true", help="Skip automated validation")

    args = parser.parse_args()

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
        **override_kwargs
    )

    print(f"\n=======================================================")
    print(f" CASHNET Synthetic Financial Data Generator V2")
    print(f" Profile : {config.profile.upper()}")
    print(f" Seed    : {config.seed}")
    print(f" Output  : {config.data_dir}")
    print(f"=======================================================")

    # Generate
    datasets = generate_all(config)

    # Export
    print(f"\n[*] Exporting V2 CSV datasets to '{config.data_dir}'...")
    manifest = export_all_datasets(datasets, config)
    print(f"  [+] CSV files exported successfully.")
    print(f"  [+] Manifest generated at '{config.data_dir}/manifests/dataset_manifest.json'")
    print(f"  [+] Quality report generated at '{config.data_dir}/manifests/data_quality_report.json'")
    print(f"  [+] Feature manifest generated at '{config.data_dir}/manifests/feature_manifest.json'")

    # Validate
    if not args.skip_validation:
        print("\n[*] Running Automated Anti-Leakage & Relational Validation Suite...")
        report = run_all_validations(datasets)
        print(report.summary())

        if not report.is_valid:
            print("\n[!] Validation failed! Please inspect the error log above.", file=sys.stderr)
            sys.exit(1)

    # Load DB
    if args.load_db:
        print(f"\n[*] Loading datasets into database ({config.db_url})...")
        success = load_into_database(datasets, db_url=config.db_url)
        if success:
            print("  [+] Database schema created and records successfully loaded!")
        else:
            print("  [X] Database loading encountered an issue.")

    print("\n[OK] CASHNET Synthetic Dataset generated and validated successfully!\n")


if __name__ == "__main__":
    main()
