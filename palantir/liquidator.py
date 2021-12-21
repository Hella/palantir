import random

from palantir.ithil import Ithil


class Liquidator:
    """
    We model liquidators as independent agents who will try to liquidate open positions with
    a fixed probability.
    """

    ithil: Ithil
    liquidation_probability: float

    def __init__(
        self,
        ithil: Ithil,
        liquidation_probability: float,
    ):

        self.ithil = ithil
        self.liquidation_probability = liquidation_probability

    def liquidate(self) -> None:
        liquidable_positions = [
            position_id
            for position_id in self.ithil.active_positions.keys()
            if self.ithil.can_liquidate_position(position_id)
        ]
        if self._will_liquidate_position():
            position_id = random.choice(liquidable_positions)
            self.ithil.liquidate_position(position_id)

    def _will_liquidate_position(self) -> bool:
        return self.liquidation_probability * 100 < random.randint(0, 100)
