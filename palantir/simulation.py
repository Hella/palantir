import logging
from typing import Dict, List

from palantir.clock import Clock
from palantir.ithil import Ithil
from palantir.oracle import PriceOracle
from palantir.trader import Trader
from palantir.types import Currency


class Simulation:
    clock: Clock
    ithil: Ithil
    traders: List[Trader]

    def __init__(
        self,
        clock: Clock,
        ithil: Ithil,
        traders: List[Trader],
    ):
        self.clock = clock
        self.ithil = ithil
        self.traders = traders

    def run(self) -> None:
        while self.clock.step():
            logging.info(f"TIME: {self.clock._time}")
            logging.info(f"POSITIONS: {self.ithil.active_positions}")
            for trader in self.traders:
                trader.trade()
            for position_id in self.ithil.active_positions.keys():
                if self.ithil.can_liquidate_position(position_id):
                    self.ithil.liquidate_position(position_id)
