"""Tests for Deterministic Reproducibility with Identical Seeds."""

import unittest
from src.synthetic_data.config import GenerationConfig
from src.synthetic_data.main import generate_all


class TestReproducibility(unittest.TestCase):
    """Test reproducibility with seeds."""

    def test_deterministic_reproducibility(self):
        """Validates that generating datasets twice with the same seed produces identical results."""
        config1 = GenerationConfig.from_profile("dev", seed=42)
        datasets1 = generate_all(config1)

        config2 = GenerationConfig.from_profile("dev", seed=42)
        datasets2 = generate_all(config2)

        for tbl in datasets1.keys():
            self.assertEqual(len(datasets1[tbl]), len(datasets2[tbl]), f"Length mismatch for table {tbl}")
            self.assertEqual(datasets1[tbl], datasets2[tbl], f"Content mismatch for table {tbl}")


if __name__ == "__main__":
    unittest.main()
