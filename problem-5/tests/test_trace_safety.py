from app.domain.runtime import RuntimeRun
from app.policy.policy import PolicyGate
from app.provider.fake import FakeModelProvider
from app.runtime.orchestrator import RuntimeOrchestrator
from app.trace.collector import TraceCollector


def test_trace_does_not_record_secret_or_hidden_reasoning():
    trace = TraceCollector()

    secret = "sk-super-secret-api-key"
    hidden_reasoning = "PRIVATE_INTERNAL_REASONING"

    provider = FakeModelProvider(
        [
            "Hello",
            " world",
        ]
    )

    run = RuntimeRun(
        user_input=f"Use this secret: {secret}"
    )

    orchestrator = RuntimeOrchestrator(
        policy_gate=PolicyGate(),
        trace=trace,
    )

    result = orchestrator.execute(
        run,
        provider,
    )

    assert result.output == "Hello world"

    serialized_trace = str(trace.events)

    assert secret not in serialized_trace
    assert hidden_reasoning not in serialized_trace

    for event in trace.events:
        assert "reasoning" not in event.details
        assert "secret" not in event.details