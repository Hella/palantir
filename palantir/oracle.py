from typing import Dict, List

from palantir.clock import Clock
from palantir.db import Quote
from palantir.types import Currency, Price


class PriceOracle:
    clock: Clock
    quotes: Dict[Currency, List[Quote]] = {}

    def __init__(self, clock: Clock, quotes: Dict[Currency, List[Quote]]) -> None:
        quote_periods = [len(prices) for prices in quotes.values()]

        assert (
            len(set(quote_periods)) == 1
        ), "All price quote series must have the same length"

        self.clock = clock
        self.quotes = quotes

    def get_price(self, token: Currency) -> Price:
        return self.quotes[token][self.clock.time].price
