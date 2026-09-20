from app.trace.events import TraceEvent


class TraceCollector:
    def __init__(self) -> None:
        self._events: list[TraceEvent] = []

    def record(self, event: TraceEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> list[TraceEvent]:
        return list(self._events)

    def event_types(self) -> list[str]:
        return [
            event.event_type
            for event in self._events
        ]