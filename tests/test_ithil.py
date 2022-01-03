from typing import List

from palantir.clock import Clock
from palantir.constants import (
    GAUSS_RANDOM_SLIPPAGE,
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
from palantir.util import Percent


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
    DAI_INSURANCE_LIQUIDITY = 1000.0
    DAI_LIQUIDITY = 750000.0
    COLLATERAL = 100.0
    PRINCIPAL = 1000.0

    quotes = {
        Currency('dai'): make_test_quotes_from_prices(
            [1.0, 1.0]
        ),
        Currency('ethereum'): make_test_quotes_from_prices(
            [4000, 4000 + Percent(10).of(4000)]
        ),
    }
    periods = len(list(quotes.values())[0])
    clock = Clock(periods)
    metrics_logger = MetricsLogger(clock)
    ithil = Ithil(
        apply_slippage=lambda price: price,  # Assume no slippage
        calculate_fees=lambda _: 0.0,
        calculate_interest_rate=lambda _src_token, _dst_token, _collateral, _principal: 0.0,
        calculate_liquidation_fee=lambda _: 0.0,
        clock=clock,
        insurance_pool={
            Currency("dai"): DAI_INSURANCE_LIQUIDITY,
        },
        metrics_logger=metrics_logger,
        price_oracle=PriceOracle(
            clock=clock,
            quotes=quotes,
        ),
        vaults={
            Currency('dai'): DAI_LIQUIDITY,
        },
    )

    position_id = ithil.open_position(
        trader=Account("0xabcd"),
        src_token=Currency("dai"),
        dst_token=Currency("ethereum"),
        collateral_token=Currency("dai"),
        collateral=COLLATERAL,
        principal=PRINCIPAL,
        max_slippage_percent=10,
    )

    assert position_id is not None
    assert position_id in ithil.positions, metrics_logger.metrics

    clock.step()

    assert ithil.can_liquidate_position(position_id) == False

    pl = ithil.close_position(position_id)

    assert pl == Percent(10).of(PRINCIPAL)
    assert ithil.vaults[Currency("dai")] == DAI_LIQUIDITY
    assert ithil.insurance_pool[Currency("dai")] == DAI_INSURANCE_LIQUIDITY


def test_trade_zero_fees_zero_interest_with_partial_loss():
    """
    Trader invests in DAI/WETH with a loss of 5%.
    Collateral of 100.0, leverage of x10.
    No fees and no interest.
    Position in closed with a loss fully covered by the collateral.
    """
    COLLATERAL = 100.0
    PRINCIPAL = 1000.0
    DAI_INSURANCE_LIQUIDITY = 1000.0
    DAI_LIQUIDITY = 750000.0

    quotes = {
        Currency("ethereum"): make_test_quotes_from_prices(
            [4400, 4400 - Percent(5).of(4400)]
        ),
        Currency("dai"): make_test_quotes_from_prices(
            [1.0, 1.0]
        )
    }
    periods = len(list(quotes.values())[0])
    clock = Clock(periods)
    metrics_logger = MetricsLogger(clock)
    ithil = Ithil(
        apply_slippage=lambda price: price,
        calculate_fees=lambda _: 0.0,
        calculate_interest_rate=lambda _src_token, _dst_token, _collateral, _principal: 0.0,
        calculate_liquidation_fee=lambda _: 0.0,
        clock=clock,
        insurance_pool={
            Currency("dai"): DAI_INSURANCE_LIQUIDITY,
        },
        metrics_logger=metrics_logger,
        price_oracle=PriceOracle(
            clock=clock,
            quotes=quotes,
        ),
        vaults={
            Currency("dai"): DAI_LIQUIDITY,
        },
    )

    position_id = ithil.open_position(
        trader=Account("0xabcd"),
        src_token=Currency("dai"),
        dst_token=Currency("ethereum"),
        collateral_token=Currency("dai"),
        collateral=COLLATERAL,
        principal=PRINCIPAL,
        max_slippage_percent=10,
    )

    assert position_id is not None
    assert position_id in ithil.active_positions

    clock.step()

    assert ithil.can_liquidate_position(position_id) == False

    pl = ithil.close_position(position_id)

    assert pl == -Percent(5).of(PRINCIPAL)
    assert ithil.vaults[Currency("dai")] == DAI_LIQUIDITY
    assert ithil.insurance_pool[Currency("dai")] == DAI_INSURANCE_LIQUIDITY


def test_trade_zero_fees_zero_interest_with_total_loss():
    """
    Trader invests in DAI/WETH with a loss of 120% of collateral.
    Collateral of 100.0, leverage of x10.
    No fees and no interest.
    Position in closed with a loss not fully covered by the collateral.
    LPs are compensated by the insurance pool.
    """
    DAI_INSURANCE_LIQUIDITY = 1000.0
    DAI_LIQUIDITY = 750000.0
    COLLATERAL = 100.0
    PRINCIPAL = 1000.0

    quotes = {
        Currency("dai"): make_test_quotes_from_prices([1.0, 1.0]),
        Currency("ethereum"): make_test_quotes_from_prices([4400, 4400 - Percent(12).of(4400)])
    }
    periods = len(list(quotes.values())[0])
    clock = Clock(periods)
    metrics_logger = MetricsLogger(clock)
    ithil = Ithil(
        apply_slippage=lambda price: price,
        calculate_fees=lambda _: 0.0,
        calculate_interest_rate=lambda _src_token, _dst_token, _collateral, _principal: 0.0,
        calculate_liquidation_fee=lambda _: 0.0,
        clock=clock,
        insurance_pool={
            Currency("dai"): DAI_INSURANCE_LIQUIDITY,
        },
        metrics_logger=metrics_logger,
        price_oracle=PriceOracle(
            clock=clock,
            quotes=quotes,
        ),
        vaults={
            Currency("dai"): DAI_LIQUIDITY,
        },
    )

    position_id = ithil.open_position(
        trader=Account("0xabcd"),
        src_token=Currency("dai"),
        dst_token=Currency("ethereum"),
        collateral_token=Currency("dai"),
        collateral=COLLATERAL,
        principal=PRINCIPAL,
        max_slippage_percent=10,
    )

    assert position_id is not None
    assert position_id in ithil.active_positions

    clock.step()

    assert ithil.can_liquidate_position(position_id) == True

    pl = ithil.close_position(position_id)

    assert pl == -COLLATERAL
    assert ithil.vaults[Currency("dai")] == DAI_LIQUIDITY

    loss = Percent(12).of(PRINCIPAL)
    assert ithil.insurance_pool[Currency("dai")] == DAI_INSURANCE_LIQUIDITY - (loss - COLLATERAL)
