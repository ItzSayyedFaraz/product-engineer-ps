from app.domain.runtime import RunStatus, RuntimeRun
from app.policy.policy import PolicyGate
from app.provider.fake import FakeModelProvider
from app.runtime.cancellation import CancellationToken
from app.runtime.clock import FakeClock
from app.runtime.orchestrator import RuntimeOrchestrator
from app.trace.collector import TraceCollector


def test_provider_failure_produces_failure_trace():
    trace = TraceCollector()

    provider = FakeModelProvider(
        ["Hello", " world"],
        fail_at_index=1,
        failure_message="provider failed",
    )

    run = RuntimeRun(
        user_input="Say hello"
    )

    orchestrator = RuntimeOrchestrator(
        policy_gate=PolicyGate(),
        trace=trace,
    )

    result = orchestrator.execute(
        run,
        provider,
    )

    assert result.status == RunStatus.FAILED

    assert trace.event_types() == [
        "RUN_STARTED",
        "POLICY_ACCEPTED",
        "PROVIDER_STARTED",
        "OUTPUT_CHUNK",
        "PROVIDER_ERROR",
    ]


def test_cancellation_produces_cancelled_trace():
    trace = TraceCollector()

    cancellation_token = CancellationToken()

    def cancel_after_first_chunk(
        index: int,
        chunk: str,
    ) -> None:
        if index == 0:
            cancellation_token.cancel()

    provider = FakeModelProvider(
        ["Hello", " world", "!"],
        on_chunk=cancel_after_first_chunk,
    )

    run = RuntimeRun(
        user_input="Say hello"
    )

    orchestrator = RuntimeOrchestrator(
        policy_gate=PolicyGate(),
        trace=trace,
    )

    result = orchestrator.execute(
        run,
        provider,
        cancellation_token,
    )

    assert result.status == RunStatus.CANCELLED

    assert trace.event_types() == [
        "RUN_STARTED",
        "POLICY_ACCEPTED",
        "PROVIDER_STARTED",
        "OUTPUT_CHUNK",
        "RUN_CANCELLED",
    ]


def test_timeout_produces_timeout_trace():
    trace = TraceCollector()

    clock = FakeClock(
        initial_time=100.0
    )

    def advance_clock(
        index: int,
        chunk: str,
    ) -> None:
        clock.advance(10)

    provider = FakeModelProvider(
        ["Hello", " world"],
        on_chunk=advance_clock,
    )

    run = RuntimeRun(
        user_input="Say hello"
    )

    orchestrator = RuntimeOrchestrator(
        policy_gate=PolicyGate(),
        clock=clock,
        trace=trace,
    )

    result = orchestrator.execute(
        run,
        provider,
        timeout_seconds=5,
    )

    assert result.status == RunStatus.TIMED_OUT

    assert trace.event_types() == [
        "RUN_STARTED",
        "POLICY_ACCEPTED",
        "PROVIDER_STARTED",
        "OUTPUT_CHUNK",
        "RUN_TIMED_OUT",
    ]