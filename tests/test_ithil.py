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


def test_trade_zero_fees_zero_interest_with_profit():
    """
    Trader invests in DAI/WETH with a profit of 10%.
    Collateral of 100.0, leverage of x10.
    No fees and no interest.
    Position in closed with a profit.
    """
    DAI_LIQUIDITY = 750000.0
    WETH_LIQUIDITY = 300.0

    quotes = {
        Currency('dai'): make_test_quotes_from_prices(
            [1.0, 1.0]
        ),
        Currency('ethereum'): make_test_quotes_from_prices(
            [4000, 4400]
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
            Currency('dai'): DAI_LIQUIDITY,
            Currency('ethereum'): WETH_LIQUIDITY,
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

    assert ithil.can_liquidate_position(position_id) == False

    pl = ithil.close_position(position_id)

    assert pl == 100.0
    assert ithil.vaults[Currency("dai")] == DAI_LIQUIDITY
    assert ithil.vaults[Currency("ethereum")] == WETH_LIQUIDITY


def test_trade_zero_fees_zero_interest_with_partial_loss():
    """
    Trader invests in DAI/WETH with a loss of 5%.
    Collateral of 100.0, leverage of x10.
    No fees and no interest.
    Position in closed with a loss fully covered by the collateral.
    """
    DAI_LIQUIDITY = 750000.0
    WETH_LIQUIDITY = 300.0

    quotes = {
        Currency("ethereum"): make_test_quotes_from_prices(
            [4400, 4180]
        ),
        Currency("dai"): make_test_quotes_from_prices(
            [1.0, 1.0]
        )
    }
    periods = len(list(quotes.values())[0])
    clock = Clock(periods)
    metrics_logger = MetricsLogger(clock)
    ithil = Ithil(
        apply_fees=NULL_FEES,
        apply_slippage=lambda price: price,
        clock=clock,
        metrics_logger=metrics_logger,
        price_oracle=PriceOracle(
            clock=clock,
            quotes=quotes,
        ),
        vaults={
            Currency("dai"): DAI_LIQUIDITY,
            Currency("ethereum"): WETH_LIQUIDITY,
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

    assert position_id in ithil.active_positions, ithil.closed_positions

    clock.step()

    assert ithil.can_liquidate_position(position_id) == False

    pl = ithil.close_position(position_id)

    assert pl == -50.0
    assert ithil.vaults[Currency("dai")] == DAI_LIQUIDITY
    assert ithil.vaults[Currency("ethereum")] == WETH_LIQUIDITY
