# CoinGecko API crawler
# https://www.coingecko.com/it/api/documentation
import logging
from datetime import datetime
from typing import Iterable, List, Tuple

import requests

from palantir.constants import SECONDS_IN_A_DAY
from palantir.types import Currency, Price, Timestamp


COINGEKO_BASE_URL = "https://api.coingecko.com/api/v3"


def coin_ids() -> Iterable[str]:
    response = requests.get(f"{COINGEKO_BASE_URL}/coins")
    data = response.json()
    for coin in data:
        yield coin["id"]


def market_chart_range(
    coin_id: Currency,
    vs_currency: Currency,
    from_timestamp: Timestamp,
    to_timestamp: Timestamp,
) -> List[Tuple[Timestamp, Price]]:
    days = int((to_timestamp - from_timestamp) / SECONDS_IN_A_DAY)
    days_per_api_call = 30
    periods = (
        int(days / days_per_api_call) + 1
    )  # Add an extra day to also download the rest
    date_ranges = [
        (
            from_timestamp + (n * days_per_api_call * SECONDS_IN_A_DAY),
            from_timestamp + ((n + 1) * days_per_api_call * SECONDS_IN_A_DAY),
        )
        for n in range(periods)
    ]

    prices = {}  # We write everything in a dict to avoid duplicate price samples
    for start, end in date_ranges:
        logging.info(
            f"Downloading {coin_id} prices {datetime.utcfromtimestamp(start).strftime('%Y-%m-%d %H:%M:%S')} => {datetime.utcfromtimestamp(end).strftime('%Y-%m-%d %H:%M:%S')}"
        )
        response = requests.get(
            f"{COINGEKO_BASE_URL}/coins/{coin_id}/market_chart/range?vs_currency={vs_currency}&from={start}&to={end}"
        )
        data = response.json()
        prices.update({timestamp: price for timestamp, price in data["prices"]})

    # Sort everything by ascending timestamp before returning
    return sorted(
        [(timestamp, price) for timestamp, price in prices.items()], key=lambda x: x[0]
    )
