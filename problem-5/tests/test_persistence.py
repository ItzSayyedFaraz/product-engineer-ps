from app.domain.runtime import RunStatus, RuntimeRun
from app.persistence.run_store import RunStore


def test_run_can_be_saved_and_loaded(tmp_path):
    store = RunStore(
        tmp_path / "runs.json"
    )

    run = RuntimeRun(
        user_input="Hello"
    )

    run.output = "Hello back"
    run.transition_to(RunStatus.COMPLETED)

    store.save(run)

    saved = store.get(run.run_id)

    assert saved is not None
    assert saved["run_id"] == run.run_id
    assert saved["user_input"] == "Hello"
    assert saved["output"] == "Hello back"
    assert saved["status"] == "completed"


def test_saving_same_run_updates_existing_record(tmp_path):
    store = RunStore(
        tmp_path / "runs.json"
    )

    run = RuntimeRun(
        user_input="Hello"
    )

    store.save(run)

    run.output = "Updated output"

    store.save(run)

    saved = store.get(run.run_id)

    assert saved["output"] == "Updated output"

    content = (tmp_path / "runs.json").read_text(
        encoding="utf-8"
    )

    assert content.count(run.run_id) == 1