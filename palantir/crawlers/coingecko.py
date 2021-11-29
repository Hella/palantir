from enum import Enum
from typing import Iterable, List, Tuple

import requests


from palantir.types import Price, Timestamp


COINGEKO_BASE_URL = "https://api.coingecko.com/api/v3"


def coin_ids() -> Iterable[str]:
    response = requests.get(f"{COINGEKO_BASE_URL}/coins")
    data = response.json()
    for coin in data:
        yield coin["id"]


class Interval(Enum):
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"


def market_chart(
    coin_id: str,
    vs_currency: str,
    days: int,
    interval: Interval,
) -> List[Tuple[Timestamp, Price]]:
    response = requests.get(
        f"{COINGEKO_BASE_URL}/coins/{coin_id}/market_chart?vs_currency={vs_currency}&days={days}&interval={interval}"
    )
    data = response.json()

    prices = data["prices"]
    _market_caps = data["market_caps"]
    _total_volumes = data["total_volumes"]

    return prices
