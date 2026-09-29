#!/usr/bin/env python3
"""CLI utility for idempotent importing of CASHNET synthetic datasets into relational database."""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backend.config import settings
from src.backend.importer.data_importer import DataImporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cashnet.cli.import")


def main() -> None:
    parser = argparse.ArgumentParser(description="CASHNET Database Import CLI")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=settings.DEFAULT_DATA_DIR,
        help="Directory containing synthetic CSV files (default: data_v2)",
    )
    parser.add_argument(
        "--wipe",
        action="store_true",
        help="Wipe existing data from tables before importing",
    )
    parser.add_argument(
        "--table",
        type=str,
        default=None,
        help="Import a specific single table (e.g. locations, accounts, complaints)",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to a specific CSV file when using --table",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Batch size for chunked insertions (default: 5000)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Run database integrity and count validation without importing",
    )

    args = parser.parse_args()
    importer = DataImporter(data_dir=args.data_dir)

    if args.validate_only:
        report = importer.validate_database_integrity()
        print("\n" + "=" * 50)
        print("DATABASE INTEGRITY AND RECORD COUNTS:")
        print(json.dumps(report, indent=2))
        print("=" * 50)
        return

    if args.table:
        count = importer.import_table(
            table_name=args.table,
            csv_path=Path(args.file) if args.file else None,
            wipe=args.wipe,
            batch_size=args.batch_size,
        )
        logger.info("Imported %d records into '%s'.", count, args.table)
    else:
        results = importer.import_all(wipe=args.wipe, batch_size=args.batch_size)
        report = importer.validate_database_integrity()
        print("\n" + "=" * 50)
        print("IMPORT COMPLETED SUMMARY:")
        print(json.dumps(results, indent=2))
        print("\nDATABASE VALIDATION REPORT:")
        print(json.dumps(report, indent=2))
        print("=" * 50)


if __name__ == "__main__":
    main()
