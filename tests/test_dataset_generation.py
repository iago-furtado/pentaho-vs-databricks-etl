"""Tests for a small temporary dataset generated with the production code."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from data_generation.generate_dataset import SCENARIOS, Scenario, generate_dataset
from data_generation.validate_dataset import validate_dataset


class DatasetGenerationTests(unittest.TestCase):
    def test_generate_and_validate_small_scenario(self) -> None:
        original = SCENARIOS["100k"]
        SCENARIOS["100k"] = Scenario(customers=10, products=5, transactions=50)
        try:
            with TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                generate_dataset("100k", root)
                validate_dataset("100k", root)
        finally:
            SCENARIOS["100k"] = original


if __name__ == "__main__":
    unittest.main()
