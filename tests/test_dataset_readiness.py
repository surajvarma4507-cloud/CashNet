"""Unit and integration test suite for CASHNET dataset readiness and integrity."""

import json
import unittest
from pathlib import Path
from scripts.audit_dataset import run_audit, load_csv_table, parse_iso


class TestDatasetReadiness(unittest.TestCase):
    """Test suite ensuring data readiness, integrity, and anti-leakage invariants."""

    @classmethod
    def setUpClass(cls):
        cls.data_dir = Path("data_v2")
        cls.audit_results = run_audit(cls.data_dir)

    def test_audit_all_critical_checks_passed(self):
        """Ensures all critical dataset checks pass without defects."""
        self.assertTrue(
            self.audit_results.get("all_critical_checks_passed"),
            f"Dataset audit failed with defects: {self.audit_results.get('identified_defects')}",
        )

    def test_primary_key_uniqueness(self):
        """Verifies that all 11 tables have strictly unique primary keys."""
        pk_checks = self.audit_results.get("primary_key_uniqueness", {})
        self.assertEqual(len(pk_checks), 11, "All 11 tables must be checked for PK uniqueness.")
        for tbl, res in pk_checks.items():
            self.assertTrue(
                res["is_unique"],
                f"Table {tbl} primary key '{res['pk_column']}' is not unique! Total: {res['total_rows']}, Unique: {res['unique_values']}"
            )

    def test_foreign_key_integrity(self):
        """Verifies that all foreign key references resolve to valid entities."""
        fk_checks = self.audit_results.get("foreign_key_integrity", {})
        for fk_name, res in fk_checks.items():
            self.assertTrue(
                res["is_valid"],
                f"Foreign key '{fk_name}' failed validation! Invalid count: {res['invalid_fk_count']}, Samples: {res['sample_invalid']}"
            )

    def test_anti_leakage_invariants(self):
        """Verifies that processed model input tables contain ZERO target columns."""
        forbidden_targets = {
            "is_synthetic_mule",
            "has_future_cashout",
            "actual_next_cashout_event_id",
            "actual_next_location_id",
            "actual_next_cashout_at",
            "actual_minutes_until_cashout",
            "actual_cashout_amount",
            "evaluation_status",
        }
        leakage_checks = self.audit_results.get("leakage_feature_audit", {}).get("table_leakage_checks", {})
        for tbl, res in leakage_checks.items():
            self.assertTrue(
                res["is_leakage_free"],
                f"Table {tbl} leaked target columns: {res['leaked_target_columns']}"
            )
            for col in res["columns"]:
                self.assertNotIn(col, forbidden_targets, f"Column '{col}' in '{tbl}' violates anti-leakage policy!")

    def test_candidate_location_coverage(self):
        """Verifies 100% presence of actual future cashout locations in candidates."""
        cov = self.audit_results.get("candidate_coverage_audit", {})
        self.assertGreater(cov.get("total_positive_future_cases", 0), 0)
        self.assertEqual(
            cov.get("missing_from_candidates", 0),
            0,
            f"Missing actual cashout locations in {cov.get('missing_from_candidates')} cases!"
        )
        self.assertEqual(cov.get("coverage_pct"), 100.0)

    def test_candidate_duplicates(self):
        """Verifies no candidate list contains duplicate ATM locations for the same snapshot."""
        dup_info = self.audit_results.get("candidate_duplicates_audit", {})
        self.assertEqual(dup_info.get("snapshots_with_duplicate_locations"), 0)

    def test_temporal_order_logic(self):
        """Verifies that all future cashout events occur strictly after complaint registration."""
        temp = self.audit_results.get("temporal_ordering_audit", {})
        self.assertTrue(
            temp.get("is_temporally_sound"),
            f"Temporal defects found: {temp.get('sample_temporal_defects')}"
        )
        self.assertEqual(temp.get("temporal_defects_count"), 0)

    def test_financial_consistency(self):
        """Verifies non-positive transaction amounts and self-transfers are absent."""
        fin = self.audit_results.get("financial_consistency_audit", {})
        self.assertTrue(
            fin.get("is_financially_consistent"),
            f"Financial defects found: {fin.get('sample_defects')}"
        )
        self.assertEqual(fin.get("financial_defects_count"), 0)

    def test_expected_background_transaction_nulls(self):
        """Verifies background transactions with null case_id are present and expected."""
        tx_audit = self.audit_results.get("transaction_audit", {})
        self.assertGreater(tx_audit.get("background_transactions_null_case_id", 0), 0)
        self.assertGreater(tx_audit.get("background_transactions_pct", 0), 0.0)


if __name__ == "__main__":
    unittest.main()
