from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4




class RunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


TERMINAL_STATES = {
    RunStatus.COMPLETED,
    RunStatus.REJECTED,
    RunStatus.CANCELLED,
    RunStatus.TIMED_OUT,
    RunStatus.FAILED,
}


ALLOWED_TRANSITIONS = {
    RunStatus.RUNNING: {
        RunStatus.COMPLETED,
        RunStatus.REJECTED,
        RunStatus.CANCELLED,
        RunStatus.TIMED_OUT,
        RunStatus.FAILED,
    },
    RunStatus.COMPLETED: set(),
    RunStatus.REJECTED: set(),
    RunStatus.CANCELLED: set(),
    RunStatus.TIMED_OUT: set(),
    RunStatus.FAILED: set(),
}


@dataclass
class RuntimeRun:
    run_id: str = field(default_factory=lambda: str(uuid4()))
    user_input: str = ""
    status: RunStatus = RunStatus.RUNNING
    output: str = ""
    error: str | None = None

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATES

    def transition_to(
        self,
        new_status: RunStatus,
        *,
        error: str | None = None,
    ) -> None:
        allowed_states = ALLOWED_TRANSITIONS[self.status]

        if new_status not in allowed_states:
            raise RuntimeError(
                f"Invalid state transition: "
                f"{self.status.value} -> {new_status.value}"
            )

        self.status = new_status

        if error is not None:
            self.error = error

    