from app.domain.runtime import RunStatus, RuntimeRun
from app.persistence.run_store import RunStore
from app.policy.policy import PolicyGate
from app.provider.fake import FakeModelProvider
from app.runtime.orchestrator import RuntimeOrchestrator


def test_completed_run_is_persisted(tmp_path):
    store = RunStore(
        tmp_path / "runs.json"
    )

    provider = FakeModelProvider(
        ["Hello", " world"]
    )

    run = RuntimeRun(
        user_input="Say hello"
    )

    orchestrator = RuntimeOrchestrator(
        policy_gate=PolicyGate(),
        run_store=store,
    )

    result = orchestrator.execute(
        run,
        provider,
    )

    assert result.status == RunStatus.COMPLETED

    saved = store.get(run.run_id)

    assert saved is not None
    assert saved["status"] == "completed"
    assert saved["output"] == "Hello world"


def test_failed_run_is_persisted(tmp_path):
    store = RunStore(
        tmp_path / "runs.json"
    )

    provider = FakeModelProvider(
        ["Hello", " world"],
        fail_at_index=1,
        failure_message="Provider unavailable",
    )

    run = RuntimeRun(
        user_input="Say hello"
    )

    orchestrator = RuntimeOrchestrator(
        policy_gate=PolicyGate(),
        run_store=store,
    )

    result = orchestrator.execute(
        run,
        provider,
    )

    assert result.status == RunStatus.FAILED

    saved = store.get(run.run_id)

    assert saved is not None
    assert saved["status"] == "failed"
    assert saved["output"] == "Hello"
    assert saved["error"] == "Provider unavailable"