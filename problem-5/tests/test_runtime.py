import pytest

from app.domain.runtime import RunStatus, RuntimeRun


def test_new_run_starts_as_running():
    run = RuntimeRun(user_input="Hello")

    assert run.status == RunStatus.RUNNING
    assert run.user_input == "Hello"
    assert run.run_id
    assert not run.is_terminal


@pytest.mark.parametrize(
    "terminal_state",
    [
        RunStatus.COMPLETED,
        RunStatus.REJECTED,
        RunStatus.CANCELLED,
        RunStatus.TIMED_OUT,
        RunStatus.FAILED,
    ],
)
def test_running_can_transition_to_any_terminal_state(terminal_state):
    run = RuntimeRun(user_input="Hello")

    run.transition_to(terminal_state)

    assert run.status == terminal_state
    assert run.is_terminal


@pytest.mark.parametrize(
    "terminal_state",
    [
        RunStatus.COMPLETED,
        RunStatus.REJECTED,
        RunStatus.CANCELLED,
        RunStatus.TIMED_OUT,
        RunStatus.FAILED,
    ],
)
def test_terminal_state_cannot_transition_again(terminal_state):
    run = RuntimeRun(user_input="Hello")

    run.transition_to(terminal_state)

    with pytest.raises(RuntimeError, match="Invalid state transition"):
        run.transition_to(RunStatus.FAILED)


def test_running_cannot_transition_to_running():
    run = RuntimeRun(user_input="Hello")

    with pytest.raises(RuntimeError, match="Invalid state transition"):
        run.transition_to(RunStatus.RUNNING)


def test_failed_run_records_error():
    run = RuntimeRun(user_input="Hello")

    run.transition_to(
        RunStatus.FAILED,
        error="Provider unavailable",
    )

    assert run.status == RunStatus.FAILED
    assert run.error == "Provider unavailable"


def test_completed_run_cannot_be_cancelled():
    run = RuntimeRun(user_input="Hello")

    run.transition_to(RunStatus.COMPLETED)

    with pytest.raises(RuntimeError):
        run.transition_to(RunStatus.CANCELLED)