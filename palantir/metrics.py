from collections import defaultdict
from enum import Enum
from typing import Dict, Tuple

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
    metrics: Dict[Tuple[int, Metric], float] = defaultdict(float)

    def __init__(self, clock: Clock):
        self.clock = clock

    def log(self, metric: Metric) -> None:
        self.metrics[self.clock.time, metric] += 1.0

    def log_sum(self, metric: Metric, value: float) -> None:
        self.metrics[self.clock.time, metric] += value
