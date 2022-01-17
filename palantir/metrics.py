from enum import Enum
from typing import Dict, List, NewType

from palantir.clock import Clock
from palantir.types import Timestamp


class Metric(Enum):
    GOVERNANCE_FEES_ETHEREUM = "governance_fees_ethereum"
    INSUFFICIENT_LIQUIDITY = "insufficient_liquidity"
    INSURANCE_POOL_LIQUIDITY_DAI = "insurance_pool_liquidity_dai"
    POSITION_CLOSED = "position_closed"
    POSITION_OPENED = "position_opened"
    TRADE_FAILED = "trade_failed"
    VAULT_LIQUIDITY_DAI = "vault_liquidity_dai"


Metrics = NewType("Metrics", Dict[Metric, Dict[Timestamp, List[float]]])


class MetricsAggregator:
    def aggregate(self, samples: List[float]) -> float:
        ...


class MetricsAggregatorSum(MetricsAggregator):
    def aggregate(self, samples: List[float]) -> float:
        return sum(samples)


class MetricsAggregatorAvg(MetricsAggregator):
    def aggregate(self, samples: List[float]) -> float:
        return sum(samples) / len(samples)


class MetricsAggregatorMax(MetricsAggregator):
    def aggregate(self, samples: List[float]) -> float:
        return max(samples)


class MetricsAggregatorMin(MetricsAggregator):
    def aggregare(self, samples: List[float]) -> float:
        return min(samples)


def make_timeseries(metrics: Metrics, metric: Metric, aggregator: MetricsAggregator, periods: int) -> List[float]:
    return [
        aggregator.aggregate(metrics[metric][t])
        if metric in metrics and t in metrics[metric] else 0.0
        for t in range(periods)
    ]


class MetricsLogger:
    clock: Clock
    metrics: Metrics

    def __init__(self, clock: Clock):
        self.clock = clock
        self.metrics = Metrics({})

    def log(self, metric: Metric, sample: float=1.0) -> None:
        if metric not in self.metrics:
            self.metrics[metric] = {}

        if self.clock.time not in self.metrics[metric]:
            self.metrics[metric][self.clock.time] = []

        self.metrics[metric][self.clock.time].append(sample)
