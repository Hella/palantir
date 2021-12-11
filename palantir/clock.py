class Clock:
    _time: int = 0
    _periods: int

    def __init__(self, periods: int):
        self._periods = periods

    def advance(self) -> bool:
        self._time += 1
        return self._time < self._periods

    @property
    def time(self) -> int:
        return self._time
