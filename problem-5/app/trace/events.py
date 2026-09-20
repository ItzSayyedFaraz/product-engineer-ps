from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class TraceEvent:
    event_type: str
    run_id: str
    timestamp: str
    details: dict


def create_trace_event(
    event_type: str,
    run_id: str,
    details: dict | None = None,
) -> TraceEvent:
    return TraceEvent(
        event_type=event_type,
        run_id=run_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        details=details or {},
    )