import logging
from typing import Callable, Dict, Optional

from palantir.clock import Clock
from palantir.metrics import Metric, MetricsLogger
from palantir.oracle import PriceOracle
from palantir.types import (
    Account,
    Currency,
    Position,
    PositionId,
    Price,
)


class Ithil:
    clock: Clock
    insurance_pool: Dict[Currency, float]
    metrics_logger: MetricsLogger
    positions_id: PositionId
    positions: Dict[PositionId, Position]
    closed_positions: Dict[PositionId, float]
    price_oracle: PriceOracle
    vaults: Dict[Currency, float]

    def __init__(
        self,
        apply_slippage: Callable[[Price], Price],
        calculate_fees: Callable[[Position], float],
        calculate_liquidation_fee: Callable[[Position], float],
        clock: Clock,
        insurance_pool: Dict[Currency, float],
        metrics_logger: MetricsLogger,
        price_oracle: PriceOracle,
        vaults: Dict[Currency, float],
    ):
        self.apply_slippage = apply_slippage
        self.calculate_fees = calculate_fees
        self.calculate_liquidation_fee = calculate_liquidation_fee
        self.closed_positions = {}
        self.clock = clock
        self.insurance_pool = insurance_pool
        self.metrics_logger = metrics_logger
        self.positions = {}
        self.positions_id = PositionId(0)
        self.price_oracle = price_oracle
        self.vaults = vaults

    def open_position(
        self,
        trader: Account,
        src_token: Currency,
        dst_token: Currency,
        collateral_token: Currency,
        collateral: float,
        principal: float,
        max_slippage_percent: float,
    ) -> Optional[PositionId]:
        amount = self._swap(
            src_token, dst_token, principal
        )

        if self.vaults[src_token] < principal:
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
            allowance=amount,
            interest_rate=0.0,
        )

        position_id = self.positions_id
        self.positions[position_id] = position
        self.positions_id = PositionId(self.positions_id + 1)
        self.vaults[src_token] -= principal

        logging.info(f"OpenPosition\t => {position}")

        return position_id

    def close_position(self, position_id: PositionId, liquidation_fee=0.0) -> float:
        position = self.active_positions[position_id]

        fees = self.calculate_fees(position)

        amount = self._swap(
            position.held_token, position.owed_token, position.allowance
        )
        assert amount > 0.0, "Swap returned negative or null amount"

        if amount + position.collateral - fees < position.principal:
            # The swapped amount plus collateral with interest and fees does not fully cover the
            # principal so we keep the full collateral.
            # A liquidator should have closed this position but the trader was faster in this case,
            # the LP had a loss so we repay it with the insurance pool.
            self.metrics_logger.log(Metric.CLOSED_WITH_LP_LOSS)
            self.vaults[position.owed_token] += position.principal
            self.insurance_pool[position.owed_token] -= position.principal - (position.collateral + amount)
            trader_pl = -position.collateral
        elif amount < position.principal and amount + position.collateral - fees >= position.principal:
            # The swapped amount plus collateral with interest and fees does cover the principal
            # but the trader made a loss, so we return only part of the collateral to the trader.
            trader_pl = amount - position.principal
            self.metrics_logger.log(Metric.CLOSED_WITH_TRADER_LOSS)
            self.vaults[position.owed_token] += position.principal
        else:
            # The swapped amount is > the original loan principal so the trader made a profit or no loss.
            # We restore the principal in the LP and return the full amount + profits.
            trader_pl = amount - position.principal - fees
            self.metrics_logger.log(Metric.CLOSED_WITH_TRADER_PROFIT)
            self.vaults[position.owed_token] += position.principal

        if liquidation_fee == 0.0:
            logging.info(f"ClosePosition\t => {position}")

        self.closed_positions[position_id] = self.clock.time

        return trader_pl

    @property
    def active_positions(self) -> Dict[PositionId, Position]:
        return {
            position_id: position
            for position_id, position in self.positions.items()
            if position_id not in self.closed_positions
        }

    def can_liquidate_position(self, position_id: PositionId) -> bool:
        active_positions = self.active_positions

        if position_id not in active_positions:
            return False

        position = active_positions[position_id]

        fees = self.calculate_fees(position)

        current_value_in_owed_tokens = self._swap(
            position.held_token,
            position.owed_token,
            position.allowance,
        )

        # XXX here we assume a fixed risk factor of 30%
        return (
            position.principal - current_value_in_owed_tokens
            > position.collateral - (30 * position.collateral / 100) - fees
        )

    def liquidate_position(self, position_id: PositionId) -> float:
        """
        Performs a margin call on an open position, returns the rewarded fees in
        the same currency as the position's collateral.
        """
        position = self.active_positions[position_id]
        liquidation_fee = self.calculate_liquidation_fee(position)
        self.close_position(position_id, liquidation_fee)
        logging.info(f"LiquidatePosition\t => {position}")

        return liquidation_fee

    def _swap(
        self, src_token: Currency, dst_token: Currency, src_token_amount: float
    ) -> float:
        src_token_price = self.price_oracle.get_price(src_token)
        dst_token_price = self.price_oracle.get_price(dst_token)

        price = src_token_price / dst_token_price

        return src_token_amount * self.apply_slippage(price)
