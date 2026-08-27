"""Generate deterministic synthetic sales datasets for the experiment."""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

SEED = 20260827
DATE_START = date(2023, 1, 1)
DATE_END = date(2025, 12, 31)


@dataclass(frozen=True)
class Scenario:
    """Row counts for one experimental scenario."""

    customers: int
    products: int
    transactions: int


SCENARIOS: dict[str, Scenario] = {
    "100k": Scenario(customers=10_000, products=2_000, transactions=100_000),
    "500k": Scenario(customers=50_000, products=10_000, transactions=500_000),
    "1m": Scenario(customers=100_000, products=20_000, transactions=1_000_000),
    "5m": Scenario(customers=500_000, products=100_000, transactions=5_000_000),
}

STATES = ("AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO")
SEGMENTS = (
    "Standard", "Premium", "Corporate", "Basic", "Silver", "Gold", "Platinum",
    "Small Business", "Enterprise",
)
CATEGORIES = (
    "Electronics", "Clothing", "Home", "Sports", "Food", "Beauty", "Books",
    "Toys", "Automotive", "Garden", "Pet Supplies", "Office", "Health", "Baby",
    "Tools", "Jewelry", "Furniture", "Music",
)
FIRST_NAMES = (
    "Alex", "Bruna", "Caio", "Daniela", "Eduardo", "Fernanda", "Gabriel",
    "Helena", "Igor", "Juliana", "Lucas", "Mariana", "Nicolas", "Olivia",
    "Paulo", "Rafaela", "Samuel", "Talita", "Vinicius", "Yasmin", "Amanda",
    "Bruno", "Camila", "Diego", "Elisa", "Felipe", "Giovana", "Henrique",
    "Isabela", "Joao", "Adriana", "Bernardo", "Carolina", "Davi", "Elaine",
    "Fabio", "Gustavo", "Hugo", "Ingrid", "Jorge", "Karen", "Leonardo",
    "Manuela", "Natalia", "Otavio", "Patricia", "Renato", "Sabrina", "Thiago",
    "Valeria", "William", "Aline", "Cesar", "Debora", "Enzo", "Flavia",
    "Guilherme", "Iara", "Leandro", "Mirela", "Noemi", "Roberto", "Tatiana",
    "Vitor", "Zelia", "Andre", "Beatriz", "Claudio", "Larissa", "Murilo",
)
LAST_NAMES = (
    "Almeida", "Barbosa", "Costa", "Dias", "Ferreira", "Gomes", "Lima",
    "Martins", "Oliveira", "Souza", "Araujo", "Cardoso", "Carvalho", "Correia",
    "Freitas", "Mendes", "Moreira", "Nascimento", "Pereira", "Ribeiro", "Rocha",
    "Rodrigues", "Santos", "Silva", "Teixeira", "Vieira", "Batista", "Campos",
    "Cavalcanti", "Monteiro", "Andrade", "Borges", "Coelho", "Duarte", "Esteves",
    "Farias", "Galvao", "Henriques", "Leal", "Machado", "Neves", "Paiva", "Queiroz",
    "Reis", "Sampaio", "Tavares", "Valente", "Xavier", "Aguiar", "Braga", "Cunha",
    "Damasceno", "Escobar", "Franco", "Guimaraes", "Lacerda", "Moraes", "Noronha",
    "Peixoto", "Quintana", "Rezende", "Sales", "Trindade", "Vasconcelos", "Werneck",
    "Zanetti", "Amaral", "Bittencourt", "Chaves", "Dantas",
)


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def report_progress(label: str, current: int, total: int, interval: int) -> None:
    if current == total or current % interval == 0:
        print(f"{label}: {current:,}/{total:,} rows")


def customer_rows(count: int, rng: random.Random) -> Iterable[list[object]]:
    for customer_id in range(1, count + 1):
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)} {customer_id}"
        yield [
            customer_id,
            name,
            rng.choice(STATES),
            rng.choices(SEGMENTS, weights=(40, 15, 5, 20, 8, 5, 3, 3, 1))[0],
        ]


def product_rows(count: int, rng: random.Random) -> Iterable[list[object]]:
    for product_id in range(1, count + 1):
        category = rng.choice(CATEGORIES)
        price = round(rng.uniform(5.0, 2_000.0), 2)
        yield [product_id, category, f"{price:.2f}"]


def transaction_rows(scenario: Scenario, rng: random.Random) -> Iterable[list[object]]:
    date_range = (DATE_END - DATE_START).days
    for transaction_id in range(1, scenario.transactions + 1):
        transaction_date = DATE_START + timedelta(days=rng.randrange(date_range + 1))
        quantity = rng.choices((1, 2, 3, 4, 5, 6, 7, 8, 9, 10), weights=(30, 25, 15, 10, 7, 4, 3, 2, 2, 2))[0]
        yield [transaction_id, rng.randint(1, scenario.customers), rng.randint(1, scenario.products), transaction_date.isoformat(), quantity]


def write_csv(path: Path, header: list[str], rows: Iterable[list[object]], total: int, label: str) -> None:
    temporary_path = path.with_suffix(".csv.tmp")
    interval = max(1, total // 20)
    try:
        with temporary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            for row_number, row in enumerate(rows, start=1):
                writer.writerow(row)
                report_progress(label, row_number, total, interval)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def generate_dataset(size: str, output_root: Path, overwrite: bool = False) -> Path:
    """Generate all CSV files for a configured size and return their directory."""
    scenario = SCENARIOS[size]
    destination = output_root / size
    if destination.exists():
        if not overwrite:
            raise FileExistsError(f"{destination} already exists. Use --overwrite to replace it.")
        for file_name in ("customers.csv", "products.csv", "transactions.csv"):
            (destination / file_name).unlink(missing_ok=True)
            (destination / f"{file_name}.tmp").unlink(missing_ok=True)
    else:
        destination.mkdir(parents=True)

    print(f"Generating scenario {size} with fixed seed {SEED}.")
    write_csv(destination / "customers.csv", ["customer_id", "customer_name", "state", "customer_segment"], customer_rows(scenario.customers, random.Random(SEED + 1)), scenario.customers, "Customers")
    write_csv(destination / "products.csv", ["product_id", "product_category", "unit_price"], product_rows(scenario.products, random.Random(SEED + 2)), scenario.products, "Products")
    write_csv(destination / "transactions.csv", ["transaction_id", "customer_id", "product_id", "transaction_date", "quantity"], transaction_rows(scenario, random.Random(SEED + 3)), scenario.transactions, "Transactions")
    print(f"Dataset created at {destination}")
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", choices=SCENARIOS, required=True, help="Dataset scenario to generate.")
    parser.add_argument("--output-root", type=Path, default=project_root() / "datasets", help="Directory that will contain scenario folders.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing scenario directory.")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    generate_dataset(arguments.size, arguments.output_root, arguments.overwrite)
