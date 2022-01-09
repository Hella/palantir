from typing import Callable

from palantir.simulation import Simulation

class Palantir:

    def __init__(
        self,
        simulation_factory: Callable[[], Simulation],
        simulations_number: int,
    ):
        self.simulation_factory = simulation_factory
        self.simulations_number = simulations_number

    def run(self):
        simulations = [self.simulation_factory() for _ in range(self.simulations_number)]
        for simulation in simulations:
            simulation.run()


