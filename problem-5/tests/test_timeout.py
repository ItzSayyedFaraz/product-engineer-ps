from app.domain.runtime import RunStatus, RuntimeRun
from app.policy.policy import PolicyGate
from app.provider.fake import FakeModelProvider
from app.runtime.clock import FakeClock
from app.runtime.orchestrator import RuntimeOrchestrator


def test_timeout_stops_streaming_and_marks_run_timed_out():
    clock = FakeClock(initial_time=100)

    def advance_after_second_chunk(index: int, chunk: str) -> None:
        if index == 1:
            clock.advance(5)

    provider = FakeModelProvider(
        ["Hello", " ", "world", "!"],
        on_chunk=advance_after_second_chunk,
    )

    run = RuntimeRun(
        user_input="Say hello"
    )

    orchestrator = RuntimeOrchestrator(
        policy_gate=PolicyGate(),
        clock=clock,
    )

    result = orchestrator.execute(
        run,
        provider,
        timeout_seconds=5,
    )

    assert result.status == RunStatus.TIMED_OUT
    assert result.output == "Hello "
    assert provider.invocation_count == 1
    assert provider.consumed_chunks == 2


def test_timeout_does_not_allow_completion_after_deadline():
    clock = FakeClock(initial_time=100)

    def advance_after_first_chunk(index: int, chunk: str) -> None:
        if index == 0:
            clock.advance(10)

    provider = FakeModelProvider(
        ["Hello", "world"],
        on_chunk=advance_after_first_chunk,
    )

    run = RuntimeRun(
        user_input="Say hello"
    )

    orchestrator = RuntimeOrchestrator(
        policy_gate=PolicyGate(),
        clock=clock,
    )

    result = orchestrator.execute(
        run,
        provider,
        timeout_seconds=5,
    )

    assert result.status == RunStatus.TIMED_OUT
    assert result.output == "Hello"
    assert provider.consumed_chunks == 1