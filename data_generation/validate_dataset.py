"""Validate a generated dataset while streaming each CSV file."""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

try:  # Supports both `python -m` and direct script execution from the repository root.
    from data_generation.generate_dataset import DATE_END, DATE_START, SCENARIOS, Scenario, project_root
except ModuleNotFoundError:  # pragma: no cover - exercised by direct command-line use.
    from generate_dataset import DATE_END, DATE_START, SCENARIOS, Scenario, project_root


def read_rows(path: Path, expected_header: list[str]):
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected_header:
            raise ValueError(f"Unexpected header in {path.name}: {reader.fieldnames}")
        yield from reader


def validate_dataset(size: str, dataset_root: Path) -> None:
    """Validate row counts, sequential IDs and value/reference ranges without storing rows."""
    scenario: Scenario = SCENARIOS[size]
    directory = dataset_root / size
    customer_count = 0
    for customer_count, row in enumerate(read_rows(directory / "customers.csv", ["customer_id", "customer_name", "state", "customer_segment"]), start=1):
        if int(row["customer_id"]) != customer_count or not row["customer_name"]:
            raise ValueError(f"Invalid customer at row {customer_count}")
    if customer_count != scenario.customers:
        raise ValueError(f"Expected {scenario.customers} customers, found {customer_count}")

    product_count = 0
    for product_count, row in enumerate(read_rows(directory / "products.csv", ["product_id", "product_category", "unit_price"]), start=1):
        if int(row["product_id"]) != product_count or float(row["unit_price"]) <= 0:
            raise ValueError(f"Invalid product at row {product_count}")
    if product_count != scenario.products:
        raise ValueError(f"Expected {scenario.products} products, found {product_count}")

    transaction_count = 0
    for transaction_count, row in enumerate(read_rows(directory / "transactions.csv", ["transaction_id", "customer_id", "product_id", "transaction_date", "quantity"]), start=1):
        transaction_date = date.fromisoformat(row["transaction_date"])
        if (int(row["transaction_id"]) != transaction_count or not 1 <= int(row["customer_id"]) <= customer_count or not 1 <= int(row["product_id"]) <= product_count or not 1 <= int(row["quantity"]) or not DATE_START <= transaction_date <= DATE_END):
            raise ValueError(f"Invalid transaction at row {transaction_count}")
    if transaction_count != scenario.transactions:
        raise ValueError(f"Expected {scenario.transactions} transactions, found {transaction_count}")
    print(f"Validation passed for {size}: {customer_count:,} customers, {product_count:,} products, {transaction_count:,} transactions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", choices=SCENARIOS, required=True)
    parser.add_argument("--dataset-root", type=Path, default=project_root() / "datasets")
    arguments = parser.parse_args()
    validate_dataset(arguments.size, arguments.dataset_root)
