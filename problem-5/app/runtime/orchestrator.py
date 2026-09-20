from app.domain.runtime import RunStatus, RuntimeRun
from app.policy.policy import PolicyGate
from app.provider.base import ModelProvider
from app.runtime.cancellation import CancellationToken
from app.runtime.clock import Clock, FakeClock
from app.persistence.run_store import RunStore
from app.trace.collector import TraceCollector
from app.trace.events import create_trace_event


class RuntimeOrchestrator:
    def __init__(
        self,
        policy_gate: PolicyGate,
        clock: Clock | None = None,
        run_store: RunStore | None = None,
        trace: TraceCollector | None = None,
    ):
        self.policy_gate = policy_gate
        self.clock = clock or FakeClock()
        self.run_store = run_store
        self.trace = trace

    # ---------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------

    def _persist(self, run: RuntimeRun) -> None:
        if self.run_store is not None:
            self.run_store.save(run)

    # ---------------------------------------------------------
    # Operational tracing
    # ---------------------------------------------------------

    def _trace(
        self,
        event_type: str,
        run: RuntimeRun,
        details: dict | None = None,
    ) -> None:
        if self.trace is not None:
            self.trace.record(
                create_trace_event(
                    event_type,
                    run.run_id,
                    details,
                )
            )

    # ---------------------------------------------------------
    # State transition + persistence
    # ---------------------------------------------------------

    def _transition(
        self,
        run: RuntimeRun,
        status: RunStatus,
        *,
        error: str | None = None,
    ) -> None:
        run.transition_to(
            status,
            error=error,
        )

        self._persist(run)

    # ---------------------------------------------------------
    # Main execution
    # ---------------------------------------------------------

    def execute(
        self,
        run: RuntimeRun,
        provider: ModelProvider,
        cancellation_token: CancellationToken | None = None,
        timeout_seconds: float | None = None,
    ) -> RuntimeRun:

        # -----------------------------------------------------
        # 0. Validate starting state
        # -----------------------------------------------------

        if run.status != RunStatus.RUNNING:
            raise RuntimeError(
                f"Cannot execute run in state: {run.status.value}"
            )

        # -----------------------------------------------------
        # 1. RUN_STARTED
        # -----------------------------------------------------

        self._trace(
            "RUN_STARTED",
            run,
        )

        # -----------------------------------------------------
        # 2. Policy check
        # -----------------------------------------------------

        decision = self.policy_gate.check(run.user_input)

        # -----------------------------------------------------
        # 3. Policy rejected
        # -----------------------------------------------------

        if not decision.allowed:

            self._trace(
                "POLICY_REJECTED",
                run,
                {
                    "reason": decision.reason,
                },
            )

            self._transition(
                run,
                RunStatus.REJECTED,
                error=decision.reason,
            )

            return run

        # -----------------------------------------------------
        # 4. Policy accepted
        # -----------------------------------------------------

        self._trace(
            "POLICY_ACCEPTED",
            run,
        )

        # -----------------------------------------------------
        # 5. Cancellation token
        # -----------------------------------------------------

        if cancellation_token is None:
            cancellation_token = CancellationToken()

        # -----------------------------------------------------
        # 6. Persist accepted running work
        # -----------------------------------------------------

        self._persist(run)

        # -----------------------------------------------------
        # 7. Already cancelled before provider starts
        # -----------------------------------------------------

        if cancellation_token.is_cancelled:

            self._trace(
                "RUN_CANCELLED",
                run,
                {
                    "reason": "cancelled_before_provider_start",
                },
            )

            self._transition(
                run,
                RunStatus.CANCELLED,
            )

            return run

        # -----------------------------------------------------
        # 8. Calculate timeout deadline
        # -----------------------------------------------------

        deadline = None

        if timeout_seconds is not None:

            if timeout_seconds < 0:
                raise ValueError(
                    "timeout_seconds cannot be negative"
                )

            deadline = self.clock.now() + timeout_seconds

        # -----------------------------------------------------
        # 9. Cooperative stop function
        # -----------------------------------------------------

        def should_stop() -> bool:

            if cancellation_token.is_cancelled:
                return True

            if (
                deadline is not None
                and self.clock.now() >= deadline
            ):
                return True

            return False

        # -----------------------------------------------------
        # 10. Provider starts
        # -----------------------------------------------------

        self._trace(
            "PROVIDER_STARTED",
            run,
        )

        # -----------------------------------------------------
        # 11. Provider execution
        # -----------------------------------------------------

        try:

            for chunk in provider.stream(
                run.user_input,
                should_stop=should_stop,
            ):

                # -------------------------------------------------
                # Cancellation has priority
                # -------------------------------------------------

                if cancellation_token.is_cancelled:

                    self._trace(
                        "RUN_CANCELLED",
                        run,
                        {
                            "reason": "cancellation_requested",
                        },
                    )

                    self._transition(
                        run,
                        RunStatus.CANCELLED,
                    )

                    return run

                # -------------------------------------------------
                # Timeout
                # -------------------------------------------------

                if (
                    deadline is not None
                    and self.clock.now() >= deadline
                ):

                    self._trace(
                        "RUN_TIMED_OUT",
                        run,
                        {
                            "reason": "execution_deadline_reached",
                        },
                    )

                    self._transition(
                        run,
                        RunStatus.TIMED_OUT,
                    )

                    return run

                # -------------------------------------------------
                # Accept output chunk
                # -------------------------------------------------

                run.output += chunk

                # -------------------------------------------------
                # Operational trace for output
                #
                # We record metadata only.
                # We do NOT expose hidden reasoning.
                # -------------------------------------------------

                self._trace(
                    "OUTPUT_CHUNK",
                    run,
                    {
                        "length": len(chunk),
                    },
                )

                # -------------------------------------------------
                # Persist partial output
                # -------------------------------------------------

                self._persist(run)

            # -----------------------------------------------------
            # 12. Provider finished
            # -----------------------------------------------------

            if cancellation_token.is_cancelled:

                self._trace(
                    "RUN_CANCELLED",
                    run,
                    {
                        "reason": "cancellation_requested",
                    },
                )

                self._transition(
                    run,
                    RunStatus.CANCELLED,
                )

                return run

            # -----------------------------------------------------
            # 13. Timeout after provider finished
            # -----------------------------------------------------

            if (
                deadline is not None
                and self.clock.now() >= deadline
            ):

                self._trace(
                    "RUN_TIMED_OUT",
                    run,
                    {
                        "reason": "execution_deadline_reached",
                    },
                )

                self._transition(
                    run,
                    RunStatus.TIMED_OUT,
                )

                return run

            # -----------------------------------------------------
            # 14. Successful completion
            # -----------------------------------------------------

            self._trace(
                "RUN_COMPLETED",
                run,
            )

            self._transition(
                run,
                RunStatus.COMPLETED,
            )

        # ---------------------------------------------------------
        # 15. Provider/runtime failure
        # ---------------------------------------------------------

        except Exception as exc:

            self._trace(
                "PROVIDER_ERROR",
                run,
                {
                    "error": str(exc),
                },
            )

            if not run.is_terminal:

                self._transition(
                    run,
                    RunStatus.FAILED,
                    error=str(exc),
                )

        # ---------------------------------------------------------
        # 16. Return final runtime state
        # ---------------------------------------------------------

        return run