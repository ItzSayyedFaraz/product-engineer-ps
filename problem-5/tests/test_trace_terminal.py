from app.trace.collector import TraceCollector
from app.trace.events import create_trace_event


def test_no_events_are_recorded_after_terminal_event():
    trace = TraceCollector()

    trace.record(
        create_trace_event(
            "RUN_STARTED",
            "run-1",
        )
    )

    trace.record(
        create_trace_event(
            "PROVIDER_STARTED",
            "run-1",
        )
    )

    trace.record(
        create_trace_event(
            "RUN_COMPLETED",
            "run-1",
        )
    )

    # This represents an invalid event after the terminal outcome.
    trace.record(
        create_trace_event(
            "OUTPUT_CHUNK",
            "run-1",
            {"length": 5},
        )
    )

    event_types = trace.event_types()

    assert event_types == [
        "RUN_STARTED",
        "PROVIDER_STARTED",
        "RUN_COMPLETED",
    ]

def test_terminal_state_is_tracked_per_run():
    trace = TraceCollector()

    trace.record(
        create_trace_event(
            "RUN_STARTED",
            "run-1",
        )
    )

    trace.record(
        create_trace_event(
            "RUN_COMPLETED",
            "run-1",
        )
    )

    # Must be ignored because run-1 is already terminal.
    trace.record(
        create_trace_event(
            "OUTPUT_CHUNK",
            "run-1",
            {"length": 5},
        )
    )

    # A different run must still work.
    trace.record(
        create_trace_event(
            "RUN_STARTED",
            "run-2",
        )
    )

    assert trace.event_types() == [
        "RUN_STARTED",
        "RUN_COMPLETED",
        "RUN_STARTED",
    ]    