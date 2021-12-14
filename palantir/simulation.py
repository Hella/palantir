import logging
from typing import Dict, List

from palantir.clock import Clock
from palantir.ithil import Ithil
from palantir.liquidator import Liquidator
from palantir.oracle import PriceOracle
from palantir.trader import Trader
from palantir.types import Currency


class Simulation:
    clock: Clock
    ithil: Ithil
    liquidators: List[Liquidator]
    traders: List[Trader]

    def __init__(
        self,
        clock: Clock,
        ithil: Ithil,
        liquidators: List[Liquidator],
        traders: List[Trader],
    ):
        self.clock = clock
        self.ithil = ithil
        self.liquidators = liquidators
        self.traders = traders

    def run(self) -> None:
        while self.clock.advance():
            logging.info(f"TIME: {self.clock._time}")
            for trader in self.traders:
                trader.trade()
            for liquidator in self.liquidators:
                liquidator.liquidate()
