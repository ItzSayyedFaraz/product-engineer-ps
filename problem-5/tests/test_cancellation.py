from app.domain.runtime import RunStatus, RuntimeRun
from app.policy.policy import PolicyGate
from app.provider.fake import FakeModelProvider
from app.runtime.cancellation import CancellationToken
from app.runtime.orchestrator import RuntimeOrchestrator


def test_cancellation_stops_streaming_and_marks_run_cancelled():
    cancellation_token = CancellationToken()

    def cancel_after_second_chunk(index: int, chunk: str) -> None:
        if index == 1:
            cancellation_token.cancel()

    provider = FakeModelProvider(
        ["Hello", " ", "world", "!"],
        on_chunk=cancel_after_second_chunk,
    )

    run = RuntimeRun(
        user_input="Say hello"
    )

    orchestrator = RuntimeOrchestrator(
        policy_gate=PolicyGate()
    )

    result = orchestrator.execute(
        run,
        provider,
        cancellation_token,
    )

    assert result.status == RunStatus.CANCELLED
    assert result.output == "Hello "
    assert provider.invocation_count == 1
    assert provider.consumed_chunks == 2


def test_cancelled_run_cannot_become_completed():
    cancellation_token = CancellationToken()
    cancellation_token.cancel()

    provider = FakeModelProvider(
        ["Hello", "world"]
    )

    run = RuntimeRun(
        user_input="Say hello"
    )

    orchestrator = RuntimeOrchestrator(
        policy_gate=PolicyGate()
    )

    result = orchestrator.execute(
        run,
        provider,
        cancellation_token,
    )

    assert result.status == RunStatus.CANCELLED
    assert result.output == ""

    # The provider must never be called.
    assert provider.invocation_count == 0