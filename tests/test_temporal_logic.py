"""Tests for Temporal Consistency and Delay Calculations."""

import unittest
from datetime import datetime
from src.synthetic_data.config import GenerationConfig
from src.synthetic_data.main import generate_all
from src.synthetic_data.validation.temporal_validation import validate_temporal_consistency


class TestTemporalLogic(unittest.TestCase):
    """Test temporal rules and ordering."""

    def test_temporal_consistency(self):
        """Validates that all temporal rules pass across complaints, transactions, and snapshots."""
        config = GenerationConfig.from_profile("dev", seed=42)
        datasets = generate_all(config)

        is_valid, errors = validate_temporal_consistency(datasets)
        self.assertTrue(is_valid, f"Temporal errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_complaint_delay_calculation(self):
        """Validates that complaint_delay_minutes matches exact timestamp differences."""
        config = GenerationConfig.from_profile("dev", seed=42)
        datasets = generate_all(config)

        for comp in datasets["complaints"]:
            t_fraud = datetime.fromisoformat(comp["fraud_occurred_at"].replace("Z", "+00:00"))
            t_comp = datetime.fromisoformat(comp["complaint_registered_at"].replace("Z", "+00:00"))
            delta_mins = int((t_comp - t_fraud).total_seconds() / 60)

            self.assertEqual(comp["complaint_delay_minutes"], delta_mins)
            self.assertGreaterEqual(t_comp, t_fraud)


if __name__ == "__main__":
    unittest.main()
