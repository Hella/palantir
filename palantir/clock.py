class Clock:
    _time: int = 0

    def tick(self) -> None:
        self._time += 1

    def tock(self) -> None:
        self._time += 1

    @property
    def time(self) -> int:
        return self._time
