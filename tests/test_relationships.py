"""Tests for Relational and Foreign-Key Integrity in Generated Datasets."""

import unittest
from src.synthetic_data.config import GenerationConfig
from src.synthetic_data.main import generate_all
from src.synthetic_data.validation.relational_validation import validate_relational_integrity


class TestRelationships(unittest.TestCase):
    """Test relational integrity of generated datasets."""

    def test_relational_integrity(self):
        """Validates that all foreign key references resolve with zero errors."""
        config = GenerationConfig.from_profile("dev", seed=42)
        datasets = generate_all(config)

        is_valid, errors = validate_relational_integrity(datasets)
        self.assertTrue(is_valid, f"Relational integrity errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_no_self_transfers(self):
        """Validates that no transaction has from_account_id == to_account_id."""
        config = GenerationConfig.from_profile("dev", seed=42)
        datasets = generate_all(config)

        for tx in datasets["transactions"]:
            self.assertNotEqual(tx["from_account_id"], tx["to_account_id"], f"Self transfer found in {tx['transaction_id']}")
            self.assertGreater(float(tx["amount"]), 0.0, f"Non-positive amount in {tx['transaction_id']}")


if __name__ == "__main__":
    unittest.main()
