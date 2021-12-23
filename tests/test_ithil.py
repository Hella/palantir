from typing import List

from palantir.clock import Clock
from palantir.constants import (
    GAUSS_RANDOM_SLIPPAGE,
    NULL_FEES,
)
from palantir.db import Quote
from palantir.ithil import Ithil
from palantir.metrics import MetricsLogger
from palantir.oracle import PriceOracle
from palantir.types import (
    Account,
    Currency,
    Price,
)


def make_test_quotes_from_prices(prices: List[Price]) -> List[Quote]:
    return [
        Quote(id=0, coin='', vs_currency='usd', timestamp=0, price=price)
        for price in prices
    ]

def test_example():
    assert True

def test_open_position():
    quotes = {
        Currency('bitcoin'): make_test_quotes_from_prices(
            [45000, 45100, 45200, 45300]
        ),
        Currency('dai'): make_test_quotes_from_prices(
            [1.0, 1.0, 1.0, 1.0]
        ),
        Currency('ethereum'): make_test_quotes_from_prices(
            [4000, 4400, 4520, 4530]
        ),
    }
    periods = len(list(quotes.values())[0])
    clock = Clock(periods)
    metrics_logger = MetricsLogger(clock)
    ithil = Ithil(
        apply_fees=NULL_FEES,
        apply_slippage=lambda price: price,  # Assume no slippage
        clock=clock,
        metrics_logger=metrics_logger,
        price_oracle=PriceOracle(
            clock=clock,
            quotes=quotes,
        ),
        vaults={
            Currency('bitcoin'): 7.0,
            Currency('dai'): 750000.0,
            Currency('ethereum'): 300.0,
        },
    )

    position_id = ithil.open_position(
        trader=Account("0xabcd"),
        src_token=Currency("dai"),
        dst_token=Currency("ethereum"),
        collateral_token=Currency("dai"),
        collateral=100.0,
        principal=1000.0,
        max_slippage_percent=10,
    )

    assert position_id is not None
    assert position_id in ithil.positions, metrics_logger.metrics

    clock.step()

    pl = ithil.close_position(position_id)

    assert pl == 100.0