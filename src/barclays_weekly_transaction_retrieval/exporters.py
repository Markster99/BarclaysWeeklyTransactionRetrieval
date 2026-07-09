from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .dates import DateWindow
from .models import TransactionRow


@dataclass(frozen=True)
class ExportResult:
    csv_path: Path
    jsonl_path: Path
    manifest_path: Path
    row_count: int


class ExportWriter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def write(
        self,
        *,
        run_id: str,
        window: DateWindow,
        rows: list[TransactionRow],
        requested_accounts: list[str],
        skipped_duplicate_count: int,
    ) -> ExportResult:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        suffix = window.filename_part()
        csv_path = self.output_dir / f"transactions_{suffix}_{run_id}.csv"
        jsonl_path = self.output_dir / f"transactions_{suffix}_{run_id}.jsonl"
        manifest_path = self.output_dir / f"manifest_{suffix}_{run_id}.json"

        self._write_csv(csv_path, rows)
        self._write_jsonl(jsonl_path, rows)
        self._write_manifest(
            manifest_path,
            run_id=run_id,
            window=window,
            requested_accounts=requested_accounts,
            row_count=len(rows),
            skipped_duplicate_count=skipped_duplicate_count,
        )

        return ExportResult(
            csv_path=csv_path,
            jsonl_path=jsonl_path,
            manifest_path=manifest_path,
            row_count=len(rows),
        )

    @staticmethod
    def _write_csv(path: Path, rows: list[TransactionRow]) -> None:
        fieldnames = list(TransactionRow.__dataclass_fields__.keys())
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row.as_dict())

    @staticmethod
    def _write_jsonl(path: Path, rows: list[TransactionRow]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row.as_dict(), ensure_ascii=False) + "\n")

    @staticmethod
    def _write_manifest(
        path: Path,
        *,
        run_id: str,
        window: DateWindow,
        requested_accounts: list[str],
        row_count: int,
        skipped_duplicate_count: int,
    ) -> None:
        window_payload = asdict(window)
        window_payload["start"] = window.start.isoformat()
        window_payload["end"] = window.end.isoformat()

        payload = {
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "window": window_payload,
            "requested_accounts": requested_accounts,
            "row_count": row_count,
            "skipped_duplicate_count": skipped_duplicate_count,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
