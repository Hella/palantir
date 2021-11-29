from collections import defaultdict
from typing import Callable, Dict

from palantir.metrics import Metric, MetricsLogger
from palantir.oracle import PriceOracle
from palantir.types import CoinId, Position, Price


class Ithil:
    metrics_logger: MetricsLogger
    positions_id: int = 0
    positions: Dict[int, Position] = {}
    price_oracle: PriceOracle
    vaults: Dict[CoinId, float] = defaultdict(float) 

    def __init__(
        self,
        apply_fees: Callable[[float], float],
        apply_slippage: Callable[[Price], Price],
        metrics_logger: MetricsLogger,
        price_oracle: PriceOracle,
    ):
        self.apply_fees = apply_fees
        self.apply_slippage = apply_slippage
        self.metrics_logger = metrics_logger
        self.price_oracle = price_oracle

    def open_position(
        self,
        trader: str, src_token: CoinId,
        dst_token: CoinId,
        collateral_token: CoinId,
        collateral: float,
        principal: float,
        max_slippage_percent: float,
    ) -> None:
        base_price = self.price_oracle.get_price(src_token, dst_token)

        price = self.apply_slippage(base_price)

        if price - base_price > max_slippage_percent * base_price / 100:
            self.metrics_logger.log(Metric.TRADE_FAILED)
            self.metrics_logger.log(Metric.SLIPPAGE_VIOLATION)
            return

        allowance = principal * price

        if self.vaults[dst_token] < principal:
            self.metrics_logger.log(Metric.TRADE_FAILED)
            self.metrics_logger.log(Metric.INSUFFICIENT_LIQUIDITY)
            return

        position = Position(
            owner=trader,
            owed_token=src_token,
            held_token=dst_token,
            collateral_token=collateral_token,
            collateral=collateral,
            principal=principal,
            allowance=allowance,
            interest_rate=0.0,
        )

        self.positions[self.positions_id] = position
        self.positions_id += 1
        self.vaults[src_token] -= principal

    def close_position(self, position_id: int) -> None:
        position = self.positions[position_id]

        base_price = self.price_oracle.get_price(
            position.held_token,
            position.owed_token,
        )

        price = self.apply_slippage(base_price)

        amount = position.allowance * price
        assert amount > 0, "Swap with negative or null output amount"

        interest = position.principal * position.interest_rate / 100
        collateral_after_interest = position.collateral - interest
        assert collateral_after_interest >= 0, "Not enough collateral to repay full interest"
        self.vaults[position.owed_token] += interest
        # TODO log interest amount
        # TODO log LP profit

        collateral_after_interest_and_fees = self.apply_fees(collateral_after_interest)
        # TODO direct fees to Ithil liquidation insurance pool
        # TODO direct fees to Ithil governance token holders to account for pl of the protocol
        # TODO log LP profit if any

        total_amont_after_interest_and_fees = amount + collateral_after_interest_and_fees

        if total_amont_after_interest_and_fees < position.principal:
            # The swapped amount plus collateral with interest and fees does not fully cover the
            # principal so we keep the full collateral.
            # A liquidator should have closed this position but the trader was faster in this case,
            # the LP had a loss so we repay it with the insurance pool.
            self.metrics_logger.log(Metric.CLOSED_WITH_LP_LOSS)
            self.vaults[position.owed_token] += total_amont_after_interest_and_fees
            # TODO extract tokens from Ithil liquidation insurance pool to cover for the position loss
        elif amount < position.principal:
            # The swapped amount plus collateral with interest and fees does cover the principal
            # but the trader made a loss, so we return only part of the collateral to the trader.
            trader_loss = position.principal - amount
            self.metrics_logger.log(Metric.CLOSED_WITH_TRADER_LOSS)
            self.vaults[position.owed_token] += position.principal
            # XXX should we log the trader's loss amount ?
        else:
            # The swapped amount is > the original loan principal so the trader made a profit or no loss.
            # We restore the principal in the LP and return the full amount + profits.
            trader_profit = amount - position.principal
            self.metrics_logger.log(Metric.CLOSED_WITH_TRADER_PROFIT)
            self.vaults[position.owed_token] += position.principal

        del self.positions[position_id]

    def can_liquidate_position(self, position_id: int) -> bool:
        return True

    def liquidate_position(self, position_id: int) -> None:
        pass
