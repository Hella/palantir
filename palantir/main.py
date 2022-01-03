import logging
import sys
import time
from random import gauss, uniform
from typing import Iterable, List

from argparse import ArgumentParser

from palantir.crawlers.coingecko import (
    coin_ids,
    market_chart_range,
)
from palantir.clock import Clock
from palantir.constants import (
    GAUSS_RANDOM_SLIPPAGE,
    SECONDS_IN_AN_HOUR,
)
from palantir.db import drop_all, init_db, Quote
from palantir.ithil import Ithil
from palantir.liquidator import Liquidator
from palantir.metrics import MetricsLogger
from palantir.oracle import PriceOracle
from palantir.simulation import Simulation
from palantir.trader import Trader
from palantir.types import Account, Currency, Timestamp


VS_CURRENCY = Currency("usd")


def setup_logger() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)


def download_price_data(token: Currency, hours: int) -> None:
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


def run_crawler():
    """
    Download price data for coin `token` for the last `days` days from Coingeko API
    """
    parser = ArgumentParser()
    parser.add_argument(
        "token", metavar="token", type=str, help="The token we need prices for"
    )
    parser.add_argument(
        "days", metavar="days", type=int, help="Number of days of historical data"
    )
    args = parser.parse_args()

    valid_coin_ids = list(coin_ids())
    valid_coin_ids_msg = f"Coin should be one of {valid_coin_ids}"

    token = args.token
    assert token in valid_coin_ids, valid_coin_ids_msg

    days = args.days

    download_price_data(token=token, hours=days * 24)


def _init_db(tokens: Iterable[Currency], hours: int):
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


def _read_quotes_from_db(db, token: Currency, hours: int) -> List[Quote]:
    return list(
        db.query(Quote).filter(Quote.coin == token).order_by(Quote.timestamp).all()
    )[-hours:]


def run_simulation():
    hours = 2000
    tokens = (
        Currency("bitcoin"),
        Currency("ethereum"),
        Currency("dai"),
    )

    setup_logger()

    db = _init_db(tokens, hours)

    clock = Clock(hours)
    metrics_logger = MetricsLogger(clock)
    price_oracle = PriceOracle(
        clock=clock,
        quotes={token: _read_quotes_from_db(db, token, hours) for token in tokens},
    )
    ithil = Ithil(
        apply_slippage=GAUSS_RANDOM_SLIPPAGE,
        calculate_fees=lambda _: 0.0,
        calculate_liquidation_fee=lambda _: 0.0,
        clock=clock,
        insurance_pool={
            Currency("bitcoin"): 0.0,
            Currency("dai"): 0.0,
            Currency("ethereum"): 0.0,
        },
        metrics_logger=metrics_logger,
        price_oracle=price_oracle,
        vaults={
            Currency("bitcoin"): 7,
            Currency("dai"): 750000.0,
            Currency("ethereum"): 300.0,
        },
    )
    simulation = Simulation(
        clock=clock,
        ithil=ithil,
        liquidators=[
            Liquidator(
                ithil=ithil,
                liquidation_probability=1.00,  # We have a sniper liquidator here!
            ),
        ],
        traders=[
            # XXX we have a lonely trader here
            Trader(
                account=Account("aaaaa"),
                open_position_probability=0.1,
                close_position_probability=0.2,
                ithil=ithil,
                calculate_collateral_usd=lambda token: (
                    abs(gauss(mu=3000, sigma=5000)) + 100.0
                )
                / price_oracle.get_price(token),
                calculate_leverage=lambda: uniform(1.0, 10.0),
            ),
        ],
    )

    simulation.run()
