"""Tests for Evaluation Ground Truth Separation and Integrity."""

import unittest
from src.synthetic_data.config import GenerationConfig
from src.synthetic_data.main import generate_all


class TestGroundTruth(unittest.TestCase):
    """Test hidden ground truth separation and format."""

    def test_ground_truth_structure_and_modes(self):
        """Validates that prediction ground truth contains valid statuses and modes."""
        config = GenerationConfig.from_profile("dev", seed=42)
        datasets = generate_all(config)

        ground_truth = datasets["prediction_ground_truth"]
        snapshots = datasets["prediction_snapshots"]

        self.assertEqual(len(ground_truth), len(snapshots))

        valid_eval_statuses = {"withdrawn_future", "already_withdrawn_past", "no_cashout_digital_only", "expired_unwithdrawn"}
        valid_modes = {"prediction", "investigation"}

        for snap in snapshots:
            self.assertIn(snap["prediction_mode"], valid_modes)

        for gt in ground_truth:
            self.assertIn(gt["evaluation_status"], valid_eval_statuses)
            if gt["has_future_cashout"]:
                self.assertIsNotNone(gt["actual_next_location_id"])
                self.assertIsNotNone(gt["actual_minutes_until_cashout"])
                self.assertGreaterEqual(gt["actual_minutes_until_cashout"], 0)
                self.assertGreater(gt["actual_cashout_amount"], 0)
                self.assertEqual(gt["evaluation_status"], "withdrawn_future")


if __name__ == "__main__":
    unittest.main()
