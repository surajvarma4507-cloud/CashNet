"""Tests for Candidate Location Coverage and Anti-Leakage Ranking."""

import unittest
from src.synthetic_data.config import GenerationConfig
from src.synthetic_data.main import generate_all


class TestCandidateCoverage(unittest.TestCase):
    """Test candidate location coverage and sorting properties."""

    def test_future_cashout_candidate_coverage(self):
        """Validates that whenever has_future_cashout is True, the actual cashout location is in location_candidates."""
        config = GenerationConfig.from_profile("small", seed=42)
        datasets = generate_all(config)

        candidates = datasets["location_candidates"]
        ground_truth = datasets["prediction_ground_truth"]

        # Build map of snapshot_id -> set of candidate location_ids
        cand_map = {}
        for c in candidates:
            cand_map.setdefault(c["snapshot_id"], set()).add(c["location_id"])

        covered_count = 0
        total_future_cashouts = 0

        for gt in ground_truth:
            if gt["has_future_cashout"]:
                total_future_cashouts += 1
                snap_id = gt["snapshot_id"]
                actual_loc_id = gt["actual_next_location_id"]
                self.assertIsNotNone(actual_loc_id)
                self.assertIn(snap_id, cand_map)
                self.assertIn(
                    actual_loc_id,
                    cand_map[snap_id],
                    f"Actual location {actual_loc_id} missing from candidates for snapshot {snap_id}"
                )
                covered_count += 1

        self.assertGreater(total_future_cashouts, 0, "Expected positive future cashout cases")
        self.assertEqual(covered_count, total_future_cashouts)

    def test_candidate_count_per_snapshot(self):
        """Validates that each snapshot has the expected number of candidate locations."""
        config = GenerationConfig.from_profile("small", seed=42)
        datasets = generate_all(config)

        candidates = datasets["location_candidates"]
        snapshots = datasets["prediction_snapshots"]

        cand_counts = {}
        for c in candidates:
            cand_counts[c["snapshot_id"]] = cand_counts.get(c["snapshot_id"], 0) + 1

        for snap in snapshots:
            snap_id = snap["snapshot_id"]
            count = cand_counts.get(snap_id, 0)
            self.assertEqual(count, config.candidates_per_snapshot)


if __name__ == "__main__":
    unittest.main()
