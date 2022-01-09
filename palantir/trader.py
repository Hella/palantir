import random
from typing import Callable, Dict, Set

from palantir.ithil import Ithil
from palantir.types import (
    Account,
    Currency,
    PositionId,
)


class Trader:
    """
    We model traders as independent agents who can occasionally open or close a position
    according to a fixed probability.
    Some traders will open/close positions very frequently, others will be more conservative.
    """
    account: Account
    close_position_probability: float
    ithil: Ithil
    liquidity: Dict[Currency, float]
    open_position_probability: float

    def __init__(
        self,
        account: Account,
        open_position_probability: float,
        close_position_probability: float,
        ithil: Ithil,
        calculate_collateral_usd: Callable[[Currency], float],
        calculate_leverage: Callable[[], float],
        liquidity: Dict[Currency, float],
    ):
        self.account = account
        self.calculate_collateral_usd = calculate_collateral_usd
        self.calculate_leverage = calculate_leverage
        self.open_position_probability = open_position_probability
        self.close_position_probability = close_position_probability
        self.ithil = ithil
        self.liquidity = liquidity

    def trade(self) -> None:
        if self._want_open_position():
            tokens = set(self.ithil.vaults.keys())
            src_token = random.choice(tuple(tokens))
            dst_token = random.choice(tuple(tokens - {src_token}))
            collateral = self.calculate_collateral_usd(src_token)
            principal = self.calculate_leverage() * collateral
            if self._can_open_position(src_token, collateral):
                position_id = self.ithil.open_position(
                    trader=self.account,
                    src_token=src_token,
                    dst_token=dst_token,
                    collateral_token=src_token,  # XXX for now always use src_token as collateral
                    collateral=collateral,
                    principal=principal,
                    max_slippage_percent=10,  # XXX use a fixed 10% slippage limit
                )
        for position_id in self.active_positions:
            if self._want_close_position():
                position = self.ithil.positions[position_id]
                trader_pl, _ = self.ithil.close_position(position_id)
                self.liquidity[position.owed_token] += trader_pl

    @property
    def active_positions(self) -> Set[PositionId]:
        return {
            position_id
            for position_id in self.ithil.active_positions
            if self.ithil.positions[position_id].owner == self.account
        }

    def _can_open_position(self, currency: Currency, amount: float) -> bool:
        return self.liquidity[currency] >= amount

    def _want_open_position(self) -> bool:
        r = random.random()
        return r < self.open_position_probability

    def _want_close_position(self) -> bool:
        r = random.random()
        return r < self.close_position_probability
