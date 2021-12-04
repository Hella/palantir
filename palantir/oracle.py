from typing import Dict, List

from palantir.clock import Clock
from palantir.types import Currency, Price


class PriceOracle:
    clock: Clock
    max_period: int = 0
    quotes: Dict[Currency, List[Price]] = {}

    def __init__(self, clock: Clock, quotes: Dict[Currency, List[Price]]) -> None:
        quote_periods = [len(prices) for _, prices in quotes]

        assert len(set(quote_periods)) == 1, "All price quote series must have the same length"

        self.clock = clock
        self.max_period = quote_periods[0]
        self.quotes = quotes

    def get_price(self, src_token: Currency, dst_token: Currency) -> Price:
        assert self.clock.time < self.max_period, "Simulation has ended"

        src_token_price = self.quotes[src_token][self.clock.time]
        dst_token_price = self.quotes[dst_token][self.clock.time]

        return src_token_price / dst_token_price
