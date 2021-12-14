import random
from typing import Callable, Set

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
    opened_positions: Set[PositionId] = set()
    closed_positions: Set[PositionId] = set()
    open_position_probability: float
    close_position_probability: float
    ithil: Ithil

    def __init__(
        self,
        account: Account,
        open_position_probability: float,
        close_position_probability: float,
        ithil: Ithil,
        calculate_collateral_usd: Callable[[Currency], float],
        calculate_leverage: Callable[[], float],
    ):
        self.account = account
        self.calculate_collateral_usd = calculate_collateral_usd
        self.calculate_leverage = calculate_leverage
        self.open_position_probability = open_position_probability
        self.close_position_probability = close_position_probability
        self.ithil = ithil

    def trade(self) -> None:
        if self._will_open_position():
            tokens = set(self.ithil.vaults.keys())
            src_token = random.choice(tuple(tokens))
            dst_token = random.choice(tuple(tokens - {src_token}))
            collateral = self.calculate_collateral_usd(src_token)
            principal = self.calculate_leverage() * collateral
            position_id = self.ithil.open_position(
                trader=self.account,
                src_token=src_token,
                dst_token=dst_token,
                collateral_token=src_token, # XXX for now always use src_token as collateral
                collateral=collateral,
                principal=principal,
                max_slippage_percent=10, # XXX use a fixed 10% slippage limit
            )
            if position_id is not None:
                # TODO log open position error
                self.opened_positions.add(position_id)
        active_positions = self.active_positions
        if self._will_close_position() and active_positions:
            position_id = random.choice(tuple(active_positions))
            self.ithil.close_position(position_id)
            self.closed_positions.add(position_id)

    @property
    def active_positions(self) -> Set[PositionId]:
        return self.opened_positions - self.closed_positions
    
    def _will_open_position(self) -> bool:
        return self.open_position_probability * 100 < random.randint(0, 100)

    def _will_close_position(self) -> bool:
        return self.close_position_probability * 100 < random.randint(0, 100)
