from app.domain.runtime import RunStatus, RuntimeRun
from app.provider.fake import FakeModelProvider
from app.runtime.orchestrator import RuntimeOrchestrator
from app.policy.policy import PolicyGate

def test_runtime_executes_provider_stream():
    provider = FakeModelProvider(
        ["Hello", " ", "world", "!"]
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

    assert result.status == RunStatus.COMPLETED
    assert result.output == "Hello world!"
    assert provider.invocation_count == 1