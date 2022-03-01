from multiprocess import Pool
from typing import Callable, List

from palantir.metrics import Metrics
from palantir.simulation import Simulation


def run_simulation(simulation: Simulation) -> Metrics:
    return simulation.run()


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
        with Pool(12) as pool:
            return pool.map(run_simulation, simulations)
