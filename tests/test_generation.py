"""Tests for CASHNET Synthetic Data Generation Engine."""

import unittest
from src.synthetic_data.config import GenerationConfig, INDIAN_METRO_CLUSTERS
from src.synthetic_data.main import generate_all


class TestGeneration(unittest.TestCase):
    """Test generation pipeline and constraints."""

    def test_generation_small_profile(self):
        """Tests data generation under small profile."""
        config = GenerationConfig.from_profile("small", seed=42)
        datasets = generate_all(config)

        self.assertIn("locations", datasets)
        self.assertIn("accounts", datasets)
        self.assertIn("complaints", datasets)
        self.assertIn("transactions", datasets)
        self.assertIn("cashout_events", datasets)
        self.assertIn("account_labels", datasets)
        self.assertIn("prediction_snapshots", datasets)
        self.assertIn("location_candidates", datasets)
        self.assertIn("case_relationships", datasets)
        self.assertIn("case_features", datasets)
        self.assertIn("prediction_ground_truth", datasets)

        # Verify counts match or exceed small profile targets
        self.assertGreaterEqual(len(datasets["locations"]), config.num_locations)
        self.assertGreaterEqual(len(datasets["accounts"]), config.num_accounts)
        self.assertEqual(len(datasets["complaints"]), config.num_complaints)
        self.assertEqual(len(datasets["transactions"]), config.num_transactions)
        self.assertEqual(len(datasets["prediction_snapshots"]), config.num_complaints)
        self.assertEqual(len(datasets["case_features"]), config.num_complaints)
        self.assertEqual(len(datasets["prediction_ground_truth"]), config.num_complaints)
        self.assertEqual(len(datasets["location_candidates"]), config.num_complaints * config.candidates_per_snapshot)

    def test_geographic_coordinates_in_india(self):
        """Tests that generated location coordinates strictly fall within India bounds and valid metro cities."""
        config = GenerationConfig.from_profile("small", seed=42)
        datasets = generate_all(config)

        valid_cities = {cluster.city for cluster in INDIAN_METRO_CLUSTERS}

        for loc in datasets["locations"]:
            lat = loc["latitude"]
            lon = loc["longitude"]
            self.assertTrue(6.0 <= lat <= 38.0, f"Latitude {lat} out of Indian bounds for {loc['location_id']}")
            self.assertTrue(68.0 <= lon <= 98.0, f"Longitude {lon} out of Indian bounds for {loc['location_id']}")
            self.assertIn(loc["city"], valid_cities)


if __name__ == "__main__":
    unittest.main()
