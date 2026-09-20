import json
from pathlib import Path

from app.trace.events import TraceEvent


class TraceStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        run_id: str,
        events: list[TraceEvent],
    ) -> None:

        records = [
            {
                "event_type": event.event_type,
                "run_id": event.run_id,
                "timestamp": event.timestamp,
                "details": event.details,
            }
            for event in events
        ]

        with self.path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                {
                    "run_id": run_id,
                    "events": records,
                },
                file,
                indent=2,
            )

    def get(
        self,
        run_id: str,
    ) -> list[dict] | None:

        if not self.path.exists():
            return None

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if data.get("run_id") != run_id:
            return None

        return data.get("events", [])