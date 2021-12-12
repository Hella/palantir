import time
from random import gauss, uniform

from argparse import ArgumentParser

from palantir.crawlers.coingecko import (
    coin_ids,
    market_chart_range,
)
from palantir.clock import Clock
from palantir.constants import (
    GAUSS_RANDOM_SLIPPAGE,
    NULL_FEES,
    SECONDS_IN_A_DAY,
)
from palantir.db import init_db, Quote
from palantir.ithil import Ithil
from palantir.liquidator import Liquidator
from palantir.metrics import MetricsLogger
from palantir.oracle import PriceOracle
from palantir.simulation import Simulation
from palantir.trader import Trader
from palantir.types import Account, Currency, Timestamp


VS_CURRENCY = Currency("usd")


def run_crawler():
    """
    Download price data for coin `token` for the last `days` days from Coingeko API
    """
    parser = ArgumentParser()
    parser.add_argument("token", metavar="token", type=str, help="The token we need prices for")
    parser.add_argument("days", metavar="days", type=int, help="Number of days of historical data")
    args = parser.parse_args()

    valid_coin_ids = list(coin_ids())
    valid_coin_ids_msg = f"Coin should be one of {valid_coin_ids}"

    token = args.token
    assert token in valid_coin_ids, valid_coin_ids_msg

    days = args.days

    now = Timestamp(time.time())
    prices = market_chart_range(
        coin_id=token,
        vs_currency=VS_CURRENCY,
        from_timestamp=now - days * SECONDS_IN_A_DAY,
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


def run_simulation():
    db = init_db()

    # XXX number of time samples to run the simulation on
    periods = 1000
    read_quotes_from_db = lambda token, samples: list(
        db
        .query(Quote)
        .filter(Quote.coin==token)
        .order_by(Quote.timestamp)
        .all()
    )[-samples:]

    clock = Clock(periods)
    metrics_logger = MetricsLogger(clock)
    ithil=Ithil(
        apply_fees=NULL_FEES,
        apply_slippage=GAUSS_RANDOM_SLIPPAGE,
        clock=clock,
        metrics_logger=metrics_logger,
        price_oracle=PriceOracle(
            clock=clock,
            quotes={
                Currency("dai"): read_quotes_from_db("dai", periods),
                Currency("ethereum"): read_quotes_from_db("ethereum", periods)
            },
        ),
        vaults={
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
                liquidation_probability=1.00, # We have a sniper liquidator here!
            ),
        ],
        traders=[
            # XXX we have a lonely trader here
            Trader(
                account=Account("aaaaa"),
                open_position_probability=0.1,
                close_position_probability=0.3,
                ithil=ithil,
                calculate_collateral_usd=lambda: abs(gauss(mu=3000, sigma=5000)) + 100.0,
                calculate_leverage=lambda: uniform(1.0, 10.0),
            ),
        ],
    )

    simulation.run()
