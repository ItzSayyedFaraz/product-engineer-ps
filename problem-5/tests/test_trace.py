from app.trace.collector import TraceCollector
from app.trace.events import create_trace_event


def test_trace_events_are_kept_in_order():
    collector = TraceCollector()

    collector.record(
        create_trace_event(
            "RUN_STARTED",
            "run-1",
        )
    )

    collector.record(
        create_trace_event(
            "PROVIDER_STARTED",
            "run-1",
        )
    )

    collector.record(
        create_trace_event(
            "RUN_COMPLETED",
            "run-1",
        )
    )

    assert collector.event_types() == [
        "RUN_STARTED",
        "PROVIDER_STARTED",
        "RUN_COMPLETED",
    ]


def test_trace_event_contains_operational_details():
    event = create_trace_event(
        "OUTPUT_CHUNK",
        "run-1",
        {
            "length": 5,
        },
    )

    assert event.event_type == "OUTPUT_CHUNK"
    assert event.run_id == "run-1"
    assert event.details["length"] == 5
    assert event.timestamp