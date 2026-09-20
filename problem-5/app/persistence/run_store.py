import json
from pathlib import Path

from app.domain.runtime import RuntimeRun, RunStatus


class RunStore:
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.file_path.exists():
            self.file_path.write_text(
                "[]",
                encoding="utf-8",
            )

    def save(self, run: RuntimeRun) -> None:
        runs = self._load()

        record = {
            "run_id": run.run_id,
            "user_input": run.user_input,
            "status": run.status.value,
            "output": run.output,
            "error": run.error,
        }

        existing_index = next(
            (
                index
                for index, existing in enumerate(runs)
                if existing["run_id"] == run.run_id
            ),
            None,
        )

        if existing_index is None:
            runs.append(record)
        else:
            runs[existing_index] = record

        self.file_path.write_text(
            json.dumps(
                runs,
                indent=2,
            ),
            encoding="utf-8",
        )

    def get(self, run_id: str) -> dict | None:
        runs = self._load()

        for run in runs:
            if run["run_id"] == run_id:
                return run

        return None

    def _load(self) -> list[dict]:
        content = self.file_path.read_text(
            encoding="utf-8"
        )

        return json.loads(content)