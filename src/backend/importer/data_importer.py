"""Idempotent batch synthetic data importer for CASHNET relational database."""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from src.backend.db.base import Base
from src.backend.db.models import (
    Account,
    AccountLabel,
    CaseFeature,
    CaseRelationship,
    CashoutEvent,
    Complaint,
    InvestigatorAction,
    Location,
    LocationCandidate,
    PredictionGroundTruth,
    PredictionSnapshot,
    Transaction,
)
from src.backend.db.session import SessionLocal, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cashnet.importer")

# Table dependency order (topological sort for FK integrity)
TABLE_IMPORT_ORDER = [
    ("locations", Location, ["raw/locations.csv", "locations.csv"]),
    ("accounts", Account, ["raw/accounts.csv", "accounts.csv"]),
    ("account_labels", AccountLabel, ["raw/account_labels.csv", "account_labels.csv"]),
    ("complaints", Complaint, ["raw/complaints.csv", "complaints.csv"]),
    ("transactions", Transaction, ["raw/transactions.csv", "transactions.csv"]),
    ("cashout_events", CashoutEvent, ["raw/cashout_events.csv", "cashout_events.csv"]),
    ("prediction_snapshots", PredictionSnapshot, ["processed/prediction_snapshots.csv", "prediction_snapshots.csv"]),
    ("location_candidates", LocationCandidate, ["processed/location_candidates.csv", "location_candidates.csv"]),
    ("case_relationships", CaseRelationship, ["raw/case_relationships.csv", "case_relationships.csv"]),
    ("case_features", CaseFeature, ["processed/case_features.csv", "case_features.csv"]),
    ("prediction_ground_truth", PredictionGroundTruth, ["evaluation/prediction_ground_truth.csv", "prediction_ground_truth.csv"]),
]

DATETIME_COLUMNS = {
    "locations": ["created_at"],
    "accounts": ["account_opened_at", "created_at"],
    "account_labels": ["label_created_at"],
    "complaints": ["fraud_occurred_at", "complaint_registered_at", "created_at"],
    "transactions": ["initiated_at", "completed_at", "created_at"],
    "cashout_events": ["cashout_occurred_at", "created_at"],
    "prediction_snapshots": ["prediction_timestamp", "created_at"],
    "location_candidates": ["created_at"],
    "case_relationships": ["relationship_created_at"],
    "case_features": ["created_at"],
    "investigator_actions": ["created_at"],
    "prediction_ground_truth": ["actual_next_cashout_at"],
}

INTEGER_COLUMNS = {
    "accounts": ["account_age_days", "baseline_transaction_count"],
    "account_labels": ["is_synthetic_mule"],
    "complaints": ["complaint_delay_minutes"],
    "cashout_events": ["minutes_since_previous_transaction"],
    "prediction_snapshots": [
        "complaint_delay_minutes",
        "minutes_since_last_transaction",
        "incoming_transaction_count_1h",
        "outgoing_transaction_count_1h",
        "incoming_transaction_count_24h",
        "outgoing_transaction_count_24h",
        "unique_incoming_sources_24h",
        "linked_account_count",
        "linked_case_count",
        "historical_cashout_count",
        "hour_of_day",
        "day_of_week",
    ],
    "location_candidates": [
        "historical_cashout_count",
        "historical_case_count",
        "candidate_rank_reference",
    ],
    "case_relationships": ["shared_transaction_count", "shared_account_count"],
    "case_features": [
        "complaint_delay_minutes",
        "transaction_count",
        "unique_account_count",
        "network_depth",
        "cashout_count",
        "distinct_cashout_locations",
    ],
    "prediction_ground_truth": ["actual_minutes_until_cashout"],
}

BOOLEAN_COLUMNS = {
    "locations": ["is_active"],
    "transactions": ["is_fraud_linked"],
    "cashout_events": ["is_future_ground_truth"],
    "prediction_ground_truth": ["has_future_cashout"],
}


class DataImporter:
    """Manages idempotent dataset ingestion and validation into relational database."""

    def __init__(self, data_dir: str = "data_v2", db_session: Optional[Session] = None):
        self.data_dir = Path(data_dir)
        self._external_session = db_session

    def get_session(self) -> Session:
        """Returns the active or a new database session."""
        if self._external_session is not None:
            return self._external_session
        return SessionLocal()

    def find_csv_path(self, table_name: str, relative_candidates: List[str]) -> Optional[Path]:
        """Locates the CSV file for a table within the data directory."""
        for candidate in relative_candidates:
            full_path = self.data_dir / candidate
            if full_path.exists():
                return full_path
            # Check direct table_name.csv
            direct_path = self.data_dir / f"{table_name}.csv"
            if direct_path.exists():
                return direct_path
        return None

    def wipe_all(self) -> Dict[str, int]:
        """Wipes all data from tables in reverse dependency order."""
        logger.warning("Wiping all existing data from CASHNET relational tables...")
        deleted_counts = {}
        session = self.get_session()
        try:
            # Clear investigator actions first
            session.query(InvestigatorAction).delete()
            # Drop in reverse topological order
            for table_name, model_cls, _ in reversed(TABLE_IMPORT_ORDER):
                count = session.query(model_cls).count()
                session.query(model_cls).delete()
                deleted_counts[table_name] = count
            session.commit()
            logger.info("Database wipe completed successfully: %s", deleted_counts)
            return deleted_counts
        except Exception as e:
            session.rollback()
            logger.error("Error during database wipe: %s", e)
            raise
        finally:
            if self._external_session is None:
                session.close()

    def wipe_table(self, table_name: str) -> int:
        """Wipes a single table."""
        model_map = {name: model for name, model, _ in TABLE_IMPORT_ORDER}
        model_map["investigator_actions"] = InvestigatorAction
        if table_name not in model_map:
            raise ValueError(f"Unknown table: {table_name}")

        model_cls = model_map[table_name]
        session = self.get_session()
        try:
            count = session.query(model_cls).count()
            session.query(model_cls).delete()
            session.commit()
            logger.info("Wiped %d rows from table '%s'", count, table_name)
            return count
        except Exception as e:
            session.rollback()
            logger.error("Error wiping table '%s': %s", table_name, e)
            raise
        finally:
            if self._external_session is None:
                session.close()

    def process_dataframe(self, table_name: str, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Sanitizes, casts types, and converts dataframe into a list of cleaned Python dictionaries."""
        records = df.to_dict(orient="records")
        cleaned_records = []

        dt_cols = set(DATETIME_COLUMNS.get(table_name, []))
        int_cols = set(INTEGER_COLUMNS.get(table_name, []))
        bool_cols = set(BOOLEAN_COLUMNS.get(table_name, []))

        for row in records:
            cleaned_row = {}
            for k, v in row.items():
                # Check for null / nan
                if v is None or (isinstance(v, float) and np.isnan(v)) or pd.isna(v):
                    cleaned_row[k] = None
                    continue

                if k in dt_cols:
                    if pd.notna(v):
                        dt = pd.to_datetime(v)
                        cleaned_row[k] = dt.to_pydatetime() if pd.notna(dt) else None
                    else:
                        cleaned_row[k] = None
                elif k in int_cols:
                    cleaned_row[k] = int(v) if v is not None and not (isinstance(v, float) and np.isnan(v)) else None
                elif k in bool_cols:
                    cleaned_row[k] = bool(v) if v is not None else False
                else:
                    cleaned_row[k] = v

            cleaned_records.append(cleaned_row)

        return cleaned_records

    def import_table(
        self,
        table_name: str,
        csv_path: Optional[Path] = None,
        wipe: bool = False,
        batch_size: int = 5000,
    ) -> int:
        """Imports a single table from CSV."""
        model_map = {name: (model, cands) for name, model, cands in TABLE_IMPORT_ORDER}
        if table_name not in model_map:
            raise ValueError(f"Unknown table name: {table_name}")

        model_cls, default_cands = model_map[table_name]
        if csv_path is None:
            csv_path = self.find_csv_path(table_name, default_cands)

        if csv_path is None or not Path(csv_path).exists():
            raise FileNotFoundError(f"CSV file for table '{table_name}' not found at {csv_path} or in {self.data_dir}")

        csv_path = Path(csv_path)
        logger.info("Importing table '%s' from %s (wipe=%s)...", table_name, csv_path, wipe)

        if wipe:
            self.wipe_table(table_name)

        session = self.get_session()
        start_time = time.time()
        total_inserted = 0

        try:
            # Read CSV in chunks
            for chunk_df in pd.read_csv(csv_path, chunksize=batch_size):
                records = self.process_dataframe(table_name, chunk_df)
                session.bulk_insert_mappings(model_cls, records)
                session.commit()
                total_inserted += len(records)

            elapsed = time.time() - start_time
            logger.info("Successfully imported %d rows into '%s' in %.2f seconds", total_inserted, table_name, elapsed)
            return total_inserted
        except Exception as e:
            session.rollback()
            logger.error("Failed to import table '%s': %s", table_name, e)
            raise
        finally:
            if self._external_session is None:
                session.close()

    def import_all(self, wipe: bool = False, batch_size: int = 5000) -> Dict[str, int]:
        """Imports all synthetic dataset tables in topological dependency order."""
        logger.info("Starting CASHNET dataset ingestion from '%s' (wipe=%s)...", self.data_dir, wipe)
        total_start = time.time()

        if wipe:
            self.wipe_all()

        results = {}
        for table_name, model_cls, candidates in TABLE_IMPORT_ORDER:
            csv_path = self.find_csv_path(table_name, candidates)
            if csv_path is None:
                logger.warning("Skipping table '%s' — CSV not found in %s", table_name, self.data_dir)
                results[table_name] = 0
                continue

            count = self.import_table(table_name, csv_path=csv_path, wipe=False, batch_size=batch_size)
            results[table_name] = count

        total_elapsed = time.time() - total_start
        logger.info("CASHNET dataset ingestion completed in %.2f seconds! Summary: %s", total_elapsed, results)
        return results

    def validate_database_integrity(self) -> Dict[str, Any]:
        """Runs post-import integrity checks on counts and foreign key relationships."""
        session = self.get_session()
        report: Dict[str, Any] = {"status": "ok", "counts": {}, "integrity_checks": {}}

        try:
            # Count records
            for table_name, model_cls, _ in TABLE_IMPORT_ORDER:
                count = session.query(model_cls).count()
                report["counts"][table_name] = count

            # Integrity check 1: Complaints with missing victim accounts
            missing_victim_accounts = (
                session.query(Complaint.case_id)
                .outerjoin(Account, Complaint.victim_account_id == Account.account_id)
                .filter(Account.account_id.is_(None))
                .count()
            )
            report["integrity_checks"]["complaints_missing_victim_account"] = missing_victim_accounts

            # Integrity check 2: Transactions with missing accounts
            missing_tx_from = (
                session.query(Transaction.transaction_id)
                .outerjoin(Account, Transaction.from_account_id == Account.account_id)
                .filter(Account.account_id.is_(None))
                .count()
            )
            report["integrity_checks"]["transactions_missing_from_account"] = missing_tx_from

            # Integrity check 3: Prediction ground truth count matching snapshots
            snapshot_count = report["counts"].get("prediction_snapshots", 0)
            ground_truth_count = report["counts"].get("prediction_ground_truth", 0)
            report["integrity_checks"]["snapshots_count"] = snapshot_count
            report["integrity_checks"]["ground_truth_count"] = ground_truth_count
            report["integrity_checks"]["snapshot_ground_truth_match"] = snapshot_count == ground_truth_count

            if missing_victim_accounts > 0 or missing_tx_from > 0:
                report["status"] = "warning"
                logger.warning("Integrity check warnings found: %s", report["integrity_checks"])
            else:
                logger.info("Database integrity checks PASSED successfully.")

            return report
        finally:
            if self._external_session is None:
                session.close()
