from collections import defaultdict
from enum import Enum
from typing import Dict, List, Tuple

from palantir.clock import Clock
from palantir.types import Timestamp


class Metric(Enum):
    CLOSED_WITH_LP_LOSS = "closed_with_lp_loss"
    CLOSED_WITH_TRADER_LOSS = "closed_with_trader_loss"
    CLOSED_WITH_TRADER_PROFIT = "closed_with_trader_profit"
    INSUFFICIENT_LIQUIDITY = "insufficient_liquidity"
    SLIPPAGE_VIOLATION = "slippage_violation"
    TRADE_FAILED = "trade_failed"


class MetricsLogger:
    clock: Clock
    metrics: Dict[Tuple[Timestamp, Metric], List[float]] = defaultdict(lambda: [])

    def __init__(self, clock: Clock):
        self.clock = clock

    def log(self, metric: Metric, sample: float=1.0) -> None:
        self.metrics[self.clock.time, metric].append(sample)


class MetricsAggregator:

    @staticmethod
    def sum(samples: List[float]) -> float:
        return sum(samples)

    @staticmethod
    def avg(samples: List[float]) -> float:
        return sum(samples) / len(samples)

    @staticmethod
    def max(samples: List[float]) -> float:
        return max(samples)

    @staticmethod
    def min(samples: List[float]) -> float:
        return min(samples)
