from app.trace.events import create_trace_event
from app.trace.trace_store import TraceStore


def test_trace_store_saves_and_loads_events(tmp_path):
    trace_path = tmp_path / "trace.json"

    store = TraceStore(trace_path)

    events = [
        create_trace_event(
            "RUN_STARTED",
            "run-1",
        ),
        create_trace_event(
            "PROVIDER_STARTED",
            "run-1",
        ),
        create_trace_event(
            "RUN_COMPLETED",
            "run-1",
        ),
    ]

    store.save(
        "run-1",
        events,
    )

    loaded = store.get("run-1")

    assert loaded is not None
    assert len(loaded) == 3

    assert loaded[0]["event_type"] == "RUN_STARTED"
    assert loaded[1]["event_type"] == "PROVIDER_STARTED"
    assert loaded[2]["event_type"] == "RUN_COMPLETED"


def test_trace_store_preserves_event_details(tmp_path):
    trace_path = tmp_path / "trace.json"

    store = TraceStore(trace_path)

    events = [
        create_trace_event(
            "OUTPUT_CHUNK",
            "run-2",
            {
                "length": 12,
            },
        )
    ]

    store.save(
        "run-2",
        events,
    )

    loaded = store.get("run-2")

    assert loaded is not None
    assert loaded[0]["run_id"] == "run-2"
    assert loaded[0]["details"]["length"] == 12
    assert loaded[0]["timestamp"]


def test_trace_store_returns_none_for_unknown_run(tmp_path):
    trace_path = tmp_path / "trace.json"

    store = TraceStore(trace_path)

    assert store.get("does-not-exist") is None