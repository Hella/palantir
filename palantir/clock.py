class Clock:
    _time: int = 0

    def advance(self) -> None:
        self._time += 1

    @property
    def time(self) -> int:
        return self._time
