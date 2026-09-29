"""Tests for Scenario Diversity, Modus Operandi and Channel Integrity."""

import unittest
from src.synthetic_data.config import GenerationConfig, FRAUD_TYPES, PAYMENT_CHANNELS
from src.synthetic_data.main import generate_all


class TestScenarios(unittest.TestCase):
    """Test scenario distributions and banking rails."""

    def test_all_scenarios_represented(self):
        """Validates that all configured Indian cybercrime scenarios are generated."""
        config = GenerationConfig.from_profile("small", seed=42)
        datasets = generate_all(config)

        complaints = datasets["complaints"]
        seen_scenarios = {c["fraud_type"] for c in complaints}
        expected_scenarios = set(FRAUD_TYPES)

        self.assertEqual(seen_scenarios, expected_scenarios)

    def test_payment_channels_and_rails(self):
        """Validates that all transactions use valid Indian payment channels."""
        config = GenerationConfig.from_profile("small", seed=42)
        datasets = generate_all(config)

        transactions = datasets["transactions"]
        seen_channels = {t["channel"] for t in transactions}
        expected_channels = set(PAYMENT_CHANNELS)

        for ch in seen_channels:
            self.assertIn(ch, expected_channels)


if __name__ == "__main__":
    unittest.main()
