"""Tests for Anti-Data Leakage and Hidden Target Isolation."""

import unittest
from src.synthetic_data.config import GenerationConfig
from src.synthetic_data.main import generate_all
from src.synthetic_data.validation.leakage_validation import validate_anti_leakage, FORBIDDEN_MODEL_INPUT_COLUMNS


class TestDataLeakage(unittest.TestCase):
    """Test data leakage prevention and target isolation."""

    def test_no_target_leakage_in_model_inputs(self):
        """Validates that prediction snapshots, candidates, and features do NOT contain any target columns."""
        config = GenerationConfig.from_profile("dev", seed=42)
        datasets = generate_all(config)

        is_valid, errors = validate_anti_leakage(datasets)
        self.assertTrue(is_valid, f"Leakage errors found: {errors}")
        self.assertEqual(len(errors), 0)

        model_input_tables = ["prediction_snapshots", "location_candidates", "case_features"]
        for tbl in model_input_tables:
            recs = datasets[tbl]
            self.assertGreater(len(recs), 0)
            cols = set(recs[0].keys())
            leaks = cols.intersection(FORBIDDEN_MODEL_INPUT_COLUMNS)
            self.assertEqual(len(leaks), 0, f"Table {tbl} contains leaked columns: {leaks}")


if __name__ == "__main__":
    unittest.main()
