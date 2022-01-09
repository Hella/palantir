import logging
import time
from typing import Iterable, List, Set

import names

from palantir.constants import SECONDS_IN_AN_HOUR
from palantir.crawlers.coingecko import (
    coin_ids,
    market_chart_range,
)
from palantir.db import drop_all, init_db, Quote
from palantir.types import (
    Currency,
    Timestamp,
)

class Percent:
    def __init__(self, percentage: float):
        self.percentage = percentage

    def of(self, total: float) -> float:
        return self.percentage * total / 100.0


def download_price_data(token: Currency, hours: int) -> None:
    VS_CURRENCY = Currency("usd")
    logging.info(f"Download {hours} price points for {token}")
    valid_coin_ids = list(coin_ids())
    valid_coin_ids_msg = f"Coin should be one of {valid_coin_ids}"

    assert token in valid_coin_ids, valid_coin_ids_msg

    now = Timestamp(time.time())
    prices = market_chart_range(
        coin_id=token,
        vs_currency=VS_CURRENCY,
        from_timestamp=now - hours * SECONDS_IN_AN_HOUR,
        to_timestamp=now,
    )

    quotes = [
        Quote(coin=token, vs_currency=VS_CURRENCY, timestamp=timestamp, price=price)
        for timestamp, price in prices
    ]

    db = init_db()

    for quote in quotes:
        db.add(quote)

    db.commit()


def init_price_db(tokens: Iterable[Currency], hours: int):
    db = init_db()

    if not all(
        db.query(Quote).filter(Quote.coin == token).count() >= hours for token in tokens
    ):
        db.close()
        drop_all()
        db = init_db()
        for token in tokens:
            download_price_data(token, hours)

    return db


def make_trader_names(n: int) -> Set[str]:
    trader_names = set()
    while len(trader_names) < n:
        name = names.get_full_name()
        trader_names.add(name)

    return trader_names


def read_quotes_from_db(db, token: Currency, hours: int) -> List[Quote]:
    return list(
        db.query(Quote).filter(Quote.coin == token).order_by(Quote.timestamp).all()
    )[-hours:]
