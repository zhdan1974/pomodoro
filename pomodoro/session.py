import json
import os
from datetime import date
from pathlib import Path


class Session:
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = os.path.expanduser("~/.pomodoro")
        self._path = Path(data_dir) / "session.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self):
        today = str(date.today())
        if self._path.exists():
            data = json.loads(self._path.read_text())
            if data.get("date") == today:
                return data
        return {"date": today, "count": 0}

    def _save(self):
        self._path.write_text(json.dumps(self._data))

    @property
    def count(self):
        return self._data["count"]

    def increment(self):
        self._data["count"] += 1
        self._save()
