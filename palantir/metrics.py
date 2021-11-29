from collections import defaultdict
from enum import Enum
from typing import Dict

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
    metrics: Dict[Metric, float] = defaultdict(float)

    def __init__(self, clock: Clock):
        self.clock = clock

    def log(self, metric: Metric) -> None:
        self.metrics[metric] += 1.0
