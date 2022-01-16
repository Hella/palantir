import logging
from typing import Dict, List

from palantir.clock import Clock
from palantir.ithil import Ithil
from palantir.metrics import Metric, Metrics
from palantir.oracle import PriceOracle
from palantir.trader import Trader
from palantir.types import Account, Currency


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

    def run(self) -> Metrics:
        while True:
            logging.info(f"TIME: {self.clock._time}")
            logging.info(f"POSITIONS: {self.ithil.active_positions}")
            for trader in self.traders:
                trader.trade()
                for position_id in trader.active_positions:
                    if self.ithil.can_liquidate_position(position_id):
                        position = self.ithil.positions[position_id]
                        trader_pl, liquidator_pl = self.ithil.liquidate_position(position_id)
                        trader.liquidity[position.owed_token] += trader_pl

            self.ithil.metrics_logger.log(
                Metric.INSURANCE_POOL_LIQUIDITY_DAI,
                self.ithil.insurance_pool[Currency("dai")],
            )
            self.ithil.metrics_logger.log(
                Metric.VAULT_LIQUIDITY_DAI,
                self.ithil.vaults[Currency("dai")],
            )

            should_continue = self.clock.step()
            if not should_continue:
                break

        return self.ithil.metrics_logger.metrics
