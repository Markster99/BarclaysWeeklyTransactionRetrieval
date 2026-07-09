from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RunState:
    path: Path
    seen_transaction_keys: set[str] = field(default_factory=set)

    @classmethod
    def load(cls, path: Path) -> "RunState":
        if not path.exists():
            return cls(path=path)

        payload = json.loads(path.read_text(encoding="utf-8"))
        values = payload.get("seen_transaction_keys", [])
        return cls(path=path, seen_transaction_keys={str(value) for value in values})

    def is_seen(self, key: str) -> bool:
        return key in self.seen_transaction_keys

    def mark_seen(self, keys: list[str]) -> None:
        self.seen_transaction_keys.update(keys)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"seen_transaction_keys": sorted(self.seen_transaction_keys)}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
