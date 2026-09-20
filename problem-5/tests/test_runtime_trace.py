from app.domain.runtime import RunStatus, RuntimeRun
from app.policy.policy import PolicyGate
from app.provider.fake import FakeModelProvider
from app.runtime.orchestrator import RuntimeOrchestrator
from app.trace.collector import TraceCollector


def test_completed_run_produces_ordered_trace():
    trace = TraceCollector()

    provider = FakeModelProvider(
        ["Hello", " world"]
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

    assert result.status == RunStatus.COMPLETED

    assert trace.event_types() == [
        "RUN_STARTED",
        "POLICY_ACCEPTED",
        "PROVIDER_STARTED",
        "OUTPUT_CHUNK",
        "OUTPUT_CHUNK",
        "RUN_COMPLETED",
    ]