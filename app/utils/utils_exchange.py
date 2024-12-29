import csv
from typing import Tuple, Optional
from pathlib import Path


def load_exchange_data() -> Tuple[dict, dict]:
    """Load exchange rates and fees from CSV files"""
    rates = {}
    fees = {}

    # Load exchange rates
    rates_file = Path("app/exchange_rates.csv")
    with open(rates_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row['currency_from']}-{row['currency_to']}"
            rates[key] = float(row["rate"])

    # Load exchange fees
    fees_file = Path("app/exchange_fees.csv")
    with open(fees_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row['currency_from']}-{row['currency_to']}"
            fees[key] = float(row["fee"])

    return rates, fees


# Cache exchange data
EXCHANGE_RATES, EXCHANGE_FEES = load_exchange_data()


def get_exchange_data(
    source: str, target: str
) -> Tuple[Optional[float], Optional[float]]:
    """Get exchange rate and fee for a currency pair"""
    key = f"{source}-{target}"
    rate = EXCHANGE_RATES.get(key)
    fee = EXCHANGE_FEES.get(key)
    return rate, fee
