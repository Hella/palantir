from typing import Callable, List

from palantir.metrics import Metrics
from palantir.simulation import Simulation


class Palantir:

    def __init__(
        self,
        simulation_factory: Callable[[], Simulation],
        simulations_number: int,
    ):
        self.simulation_factory = simulation_factory
        self.simulations_number = simulations_number

    def run(self) -> List[Metrics]:
        simulations = [self.simulation_factory() for _ in range(self.simulations_number)]
        return [simulation.run() for simulation in simulations]
