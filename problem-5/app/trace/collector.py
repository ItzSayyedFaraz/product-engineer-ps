from app.trace.events import TraceEvent


TERMINAL_EVENTS = {
    "RUN_COMPLETED",
    "RUN_REJECTED",
    "RUN_CANCELLED",
    "RUN_TIMED_OUT",
    "RUN_FAILED",
}


class TraceCollector:
    def __init__(self) -> None:
        self._events: list[TraceEvent] = []
        self._terminal_runs: set[str] = set()

    def record(self, event: TraceEvent) -> None:
        # Ignore any event that arrives after the run has reached
        # a terminal outcome.
        if event.run_id in self._terminal_runs:
            return

        self._events.append(event)

        if event.event_type in TERMINAL_EVENTS:
            self._terminal_runs.add(event.run_id)

    @property
    def events(self) -> list[TraceEvent]:
        return list(self._events)

    def event_types(self) -> list[str]:
        return [
            event.event_type
            for event in self._events
        ]