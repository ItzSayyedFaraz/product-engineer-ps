from app.domain.runtime import RunStatus, RuntimeRun
from app.policy.policy import PolicyGate
from app.provider.base import ModelProvider
from app.runtime.cancellation import CancellationToken
from app.runtime.clock import Clock, FakeClock


class RuntimeOrchestrator:
    def __init__(
        self,
        policy_gate: PolicyGate,
        clock: Clock | None = None,
    ):
        self.policy_gate = policy_gate
        self.clock = clock or FakeClock()

    def execute(
        self,
        run: RuntimeRun,
        provider: ModelProvider,
        cancellation_token: CancellationToken | None = None,
        timeout_seconds: float | None = None,
    ) -> RuntimeRun:

        if run.status != RunStatus.RUNNING:
            raise RuntimeError(
                f"Cannot execute run in state: {run.status.value}"
            )

        decision = self.policy_gate.check(run.user_input)

        if not decision.allowed:
            run.transition_to(
                RunStatus.REJECTED,
                error=decision.reason,
            )
            return run

        if cancellation_token is None:
            cancellation_token = CancellationToken()

        if cancellation_token.is_cancelled:
            run.transition_to(RunStatus.CANCELLED)
            return run

        deadline = None

        if timeout_seconds is not None:
            if timeout_seconds < 0:
                raise ValueError("timeout_seconds cannot be negative")

            deadline = self.clock.now() + timeout_seconds

        def should_stop() -> bool:
            if cancellation_token.is_cancelled:
                return True

            if deadline is not None and self.clock.now() >= deadline:
                return True

            return False

        try:
            for chunk in provider.stream(
                run.user_input,
                should_stop=should_stop,
            ):
                if cancellation_token.is_cancelled:
                    run.transition_to(RunStatus.CANCELLED)
                    return run

                if deadline is not None and self.clock.now() >= deadline:
                    run.transition_to(RunStatus.TIMED_OUT)
                    return run

                run.output += chunk

            if cancellation_token.is_cancelled:
                run.transition_to(RunStatus.CANCELLED)
                return run

            if deadline is not None and self.clock.now() >= deadline:
                run.transition_to(RunStatus.TIMED_OUT)
                return run

            run.transition_to(RunStatus.COMPLETED)

        except Exception as exc:
            if not run.is_terminal:
                run.transition_to(
                    RunStatus.FAILED,
                    error=str(exc),
                )

        return run