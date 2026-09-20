class Clock:
    def now(self) -> float:
        raise NotImplementedError


class FakeClock(Clock):
    def __init__(self, initial_time: float = 0.0):
        self._time = initial_time

    def now(self) -> float:
        return self._time

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("Cannot move clock backwards")

        self._time += seconds