from app.domain.runtime import RunStatus, RuntimeRun
from app.policy.policy import PolicyGate
from app.provider.fake import FakeModelProvider
from app.runtime.orchestrator import RuntimeOrchestrator


def test_provider_failure_after_partial_output_marks_run_failed():
    provider = FakeModelProvider(
        ["Hello", " ", "world", "!"],
        fail_at_index=2,
        failure_message="Provider connection lost",
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
    )

    assert result.status == RunStatus.FAILED
    assert result.output == "Hello "
    assert result.error == "Provider connection lost"

    assert provider.invocation_count == 1
    assert provider.consumed_chunks == 2

def test_failed_run_cannot_become_completed():
    provider = FakeModelProvider(
        ["Hello", "world"],
        fail_at_index=1,
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
    )

    assert result.status == RunStatus.FAILED

    # A terminal FAILED state cannot transition to COMPLETED.
    try:
        result.transition_to(RunStatus.COMPLETED)
        assert False, "FAILED run became COMPLETED"
    except RuntimeError:
        pass    