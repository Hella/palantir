import logging
import sys
from random import gauss, uniform
from typing import Tuple

from argparse import ArgumentParser

from palantir.crawlers.coingecko import (
    coin_ids,
)
from palantir.clock import Clock
from palantir.ithil import Ithil
from palantir.metrics import (
    Metric,
    MetricsAggregator,
    MetricsAggregatorSum,
    MetricsLogger,
    make_timeseries,
)
from palantir.oracle import PriceOracle
from palantir.palantir import Palantir
from palantir.simulation import Simulation
from palantir.trader import Trader
from palantir.types import Account, Currency, Position
from palantir.util import (
    download_price_data,
    init_price_db,
    make_trader_names,
    read_quotes_from_db,
)


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


HOURS = 2000
TOKENS = [
    Currency("bitcoin"),
    Currency("ethereum"),
    Currency("dai"),
]


db = init_price_db(TOKENS, HOURS)


def slippage(price: float) -> float:
    # We model slippage as a normally distributed random variable with mean equal to the current price
    # and variance proportional to a percentage of the price as described by max desired slippage.
    DESIRED_MAX_SLIPPAGE_PERCENT = 1.0
    return gauss(price, price * DESIRED_MAX_SLIPPAGE_PERCENT / 100.0)


def calculate_fees(position: Position) -> float:
    return 0.0


def calculate_interest_rate(
    src_token: Currency,
    dst_token: Currency,
    collateral: float,
    principal: float,
) -> float:
    return 0.0


def calculate_liquidation_fee(position: Position) -> float:
    return 0.0


def split_fees(fees: float) -> Tuple[float, float]:
    return (fees / 2.0, fees / 2.0)


def calculate_collateral_usd(price_oracle: PriceOracle, token: Currency) -> float:
    return (abs(gauss(mu=3000, sigma=5000)) + 100.0) / price_oracle.get_price(token)


def calculate_leverage() -> float:
    return uniform(1.0, 10.0)


def build_simulation():
    TRADERS_NUMBER = 10
    TRADER_NAMES = make_trader_names(TRADERS_NUMBER)

    clock = Clock(HOURS)

    metrics_logger = MetricsLogger(clock)
    price_oracle = PriceOracle(
        clock=clock,
        quotes={token: read_quotes_from_db(db, token, HOURS) for token in TOKENS},
    )
    ithil = Ithil(
        apply_slippage=slippage,
        calculate_fees=calculate_fees,
        calculate_interest_rate=calculate_interest_rate,
        calculate_liquidation_fee=calculate_liquidation_fee,
        clock=clock,
        insurance_pool={
            Currency("bitcoin"): 0.0,
            Currency("dai"): 0.0,
            Currency("ethereum"): 0.0,
        },
        metrics_logger=metrics_logger,
        price_oracle=price_oracle,
        split_fees=split_fees,
        vaults={
            Currency("bitcoin"): 7.0,
            Currency("dai"): 750000.0,
            Currency("ethereum"): 300.0,
        },
    )
    simulation = Simulation(
        clock=clock,
        ithil=ithil,
        traders=[
            Trader(
                account=Account(trader_name),
                open_position_probability=0.1,
                close_position_probability=0.1,
                ithil=ithil,
                calculate_collateral_usd=calculate_collateral_usd,
                calculate_leverage=calculate_leverage,
                liquidity={
                    Currency("bitcoin"): 0.0,
                    Currency("dai"): 1000.0,
                    Currency("ethereum"): 1.0,
                },
            )
            for trader_name in TRADER_NAMES
        ],
    )

    return simulation


def run_simulation():
    setup_logger()

    palantir = Palantir(
        simulation_factory=build_simulation,
        simulations_number=1,
    )

    simulations_metrics = palantir.run()
    metrics = simulations_metrics[0]

    opened_positions = make_timeseries(metrics, Metric.POSITION_OPENED, MetricsAggregatorSum(), HOURS)

    print(f"OPENED_POSITIONS => {opened_positions}")
