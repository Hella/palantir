class Percent:
    def __init__(self, percentage: float):
        self.percentage = percentage

    def of(self, total: float) -> float:
        return self.percentage * total / 100.0
