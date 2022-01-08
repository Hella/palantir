import logging
from collections import defaultdict
from typing import Callable, Dict, Optional, Tuple

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
        calculate_interest_rate: Callable[[Currency, Currency, float, float], float],
        calculate_liquidation_fee: Callable[[Position], float],
        clock: Clock,
        insurance_pool: Dict[Currency, float],
        metrics_logger: MetricsLogger,
        price_oracle: PriceOracle,
        split_fees: Callable[[float], Tuple[float, float]],
        vaults: Dict[Currency, float],
    ):
        """
        - apply_slippage: returns a new price by applying a slippage to the input price.
        - calculate_fees: calculate fees from a position, in the same currency as the position's collateral.
        - calculate_interest_rate: returns the interest rate as a decimal percentage, expressed in the same
        currency as the position's collateral.
        - calculate_liquidation_fee: returns the fee to be rewarded to the liquidator, to be deducted from
        the position's collateral, and in the same currency as the collateral.
        - clock: the clock that tracks time during the simulation, with time expressed as integers.
        - governance_pool: a virtual pool representing the liquidity sent to governance token holders.
        - insurance_pool: amount of liquidity available per currency in the insurance pool.
        - metrics_logger: used to log interesting events during a simulation.
        - price_oracle: provides current price information on a currency relative to USD.
        - split_fees: returns the original fees split into (governance_fees, insurance_fees).
        - valults: amount of liquidity available per currency in the vaults.
        """
        self.apply_slippage = apply_slippage
        self.calculate_fees = calculate_fees
        self.calculate_interest_rate = calculate_interest_rate
        self.calculate_liquidation_fee = calculate_liquidation_fee
        self.closed_positions = {}
        self.clock = clock
        self.governance_pool = defaultdict(lambda: 0.0)
        self.insurance_pool = insurance_pool
        self.metrics_logger = metrics_logger
        self.positions = {}
        self.positions_id = PositionId(0)
        self.price_oracle = price_oracle
        self.split_fees = split_fees
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

        interest_rate = self.calculate_interest_rate(src_token, dst_token, collateral, principal)

        position = Position(
            owner=trader,
            owed_token=src_token,
            held_token=dst_token,
            collateral_token=collateral_token,
            collateral=collateral,
            principal=principal,
            allowance=amount,
            interest_rate=interest_rate,
            created_at=self.clock.time,
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
        governance_fees, insurance_fees = self.split_fees(fees)
        all_fees = fees + liquidation_fee

        interest = self.calculate_interest(position)

        amount = self._swap(
            position.held_token, position.owed_token, position.allowance
        )
        assert amount > 0.0, "Swap returned negative or null amount"

        total_position_liquidity = amount + position.collateral

        # 0. Return either the original principal to liquidity providers or all remaining amount
        liquidity_pool_amount = min(position.principal, total_position_liquidity)
        remaining_position_liquidity = total_position_liquidity - liquidity_pool_amount

        # 1. Pay missing liquidity if any from the insurance pool
        insurance_amount = min(self.insurance_pool[position.owed_token], position.principal - liquidity_pool_amount)

        # 2. Pay interest rate to liquidity pool
        interest_amount = min(interest, remaining_position_liquidity)
        remaining_position_liquidity = remaining_position_liquidity - interest_amount

        # 3. Pay insurance pool fees
        insurance_fees_amount = min(insurance_fees, remaining_position_liquidity)
        remaining_position_liquidity = remaining_position_liquidity - insurance_fees_amount

        # 4. Pay governance fees
        governance_fees_amount = min(governance_fees, remaining_position_liquidity)
        remaining_position_liquidity = remaining_position_liquidity - governance_fees_amount

        # 5. Calculate trader's P&L based on remaining liquidity
        pl = remaining_position_liquidity - position.collateral

        self.vaults[position.owed_token] += liquidity_pool_amount  # The liquidity used as principal is returned to the LPs
        self.vaults[position.owed_token] += insurance_amount  # The amount of insurance used to repay the losses, if any
        self.vaults[position.owed_token] += interest_amount  # The interest amount is added to the LP
        self.insurance_pool[position.owed_token] -= insurance_amount  # The insurance amount is deducted from the IP
        self.insurance_pool[position.owed_token] += insurance_fees_amount  # The insurance fees are added to the IP
        self.governance_pool[position.owed_token] += governance_fees_amount  # The governance fees are sent to the token holders

        if liquidation_fee == 0.0:
            logging.info(f"ClosePosition\t => {position}")

        self.closed_positions[position_id] = self.clock.time

        return pl

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

    def calculate_interest(self, position: Position) -> float:
        """
        Returns interest amount in the same currency as the
        position's principal.
        """
        hours = self.clock.time - position.created_at
        if hours == 0:
            return 0.0

        p = position.principal
        r = position.interest_rate
        n = hours / (365 * 24)

        return p * r * n

    def liquidate_position(self, position_id: PositionId) -> float:
        """
        Performs a margin call on an open position, returns the rewarded fees in
        the same currency as the position's collateral.
        """
        assert self.can_liquidate_position(position_id)
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
