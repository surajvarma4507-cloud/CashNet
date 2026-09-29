"""Tests for Configuration Profiles (Small, Standard, Large)."""

import unittest
from pathlib import Path
from src.synthetic_data.config import GenerationConfig


class TestProfiles(unittest.TestCase):
    """Test configuration profiles instantiation and validation."""

    def test_small_profile_defaults(self):
        """Tests small profile default counts and parameters."""
        config = GenerationConfig.from_profile("small")
        self.assertEqual(config.profile, "small")
        self.assertEqual(config.num_complaints, 300)
        self.assertEqual(config.num_accounts, 800)
        self.assertEqual(config.num_transactions, 4000)
        self.assertEqual(config.num_locations, 60)
        self.assertEqual(config.candidates_per_snapshot, 6)
        self.assertEqual(config.data_dir, Path("data_v2"))

    def test_standard_profile_defaults(self):
        """Tests standard profile default counts and parameters."""
        config = GenerationConfig.from_profile("standard")
        self.assertEqual(config.profile, "standard")
        self.assertEqual(config.num_complaints, 5000)
        self.assertEqual(config.num_accounts, 10000)
        self.assertEqual(config.num_transactions, 65000)
        self.assertEqual(config.num_locations, 300)
        self.assertEqual(config.candidates_per_snapshot, 7)
        self.assertEqual(config.data_dir, Path("data_v2"))

    def test_large_profile_defaults(self):
        """Tests large profile default counts and parameters."""
        config = GenerationConfig.from_profile("large")
        self.assertEqual(config.profile, "large")
        self.assertEqual(config.num_complaints, 15000)
        self.assertEqual(config.num_accounts, 25000)
        self.assertEqual(config.num_transactions, 180000)
        self.assertEqual(config.num_locations, 600)
        self.assertEqual(config.candidates_per_snapshot, 8)
        self.assertEqual(config.data_dir, Path("data_v2"))

    def test_profile_aliases(self):
        """Tests alias profiles (dev, demo)."""
        config_dev = GenerationConfig.from_profile("dev")
        self.assertEqual(config_dev.profile, "small")

        config_demo = GenerationConfig.from_profile("demo")
        self.assertEqual(config_demo.profile, "standard")


if __name__ == "__main__":
    unittest.main()
