from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path


def _json_default(obj):
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "value"):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


class AuditLogger:
    def __init__(self, path: str = "audit.log"):
        self.path = Path(path)

    def write(self, event: str, payload: dict) -> None:
        record = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, "payload": payload}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=_json_default) + "\n")
