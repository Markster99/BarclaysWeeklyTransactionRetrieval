from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date, datetime

from .config import Settings
from .dates import custom_window, resolve_window
from .exceptions import BarclaysRetrievalError
from .pipeline import WeeklyTransactionPipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="barclays-weekly",
        description="Retrieve Barclays transactions for scheduled finance review.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--window", choices=["previous-week", "previous-month"], default="previous-week")
    run_parser.add_argument("--from-date", help="Inclusive start date in YYYY-MM-DD format")
    run_parser.add_argument("--to-date", help="Exclusive end date in YYYY-MM-DD format")
    run_parser.add_argument("--mock", action="store_true", help="Run with bundled mock data")

    window_parser = subparsers.add_parser("window")
    window_parser.add_argument("--mode", choices=["previous-week", "previous-month"], default="previous-week")
    window_parser.add_argument("--as-of", help="Reference date in YYYY-MM-DD format")

    subparsers.add_parser("doctor")

    args = parser.parse_args()

    try:
        if args.command == "window":
            as_of = _parse_date(args.as_of) if args.as_of else date.today()
            window = resolve_window(args.mode, as_of=as_of)
            print(json.dumps(_window_payload(window), indent=2))
            return

        settings = Settings.from_env()

        if args.command == "doctor":
            print(json.dumps(_redacted_settings(settings), indent=2, default=str))
            return

        if args.command == "run":
            window = _run_window(args)
            result = WeeklyTransactionPipeline(settings, use_mock=args.mock).run(window)
            print(
                json.dumps(
                    {
                        "run_id": result.run_id,
                        "requested_accounts": result.requested_accounts,
                        "fetched_rows": result.fetched_rows,
                        "exported_rows": result.exported_rows,
                        "skipped_duplicate_count": result.skipped_duplicate_count,
                        "csv_path": str(result.export.csv_path),
                        "jsonl_path": str(result.export.jsonl_path),
                        "manifest_path": str(result.export.manifest_path),
                    },
                    indent=2,
                )
            )
            return

    except BarclaysRetrievalError as exc:
        raise SystemExit(f"Error: {exc}") from exc


def _run_window(args: argparse.Namespace):
    if args.from_date or args.to_date:
        if not args.from_date or not args.to_date:
            raise SystemExit("Use both --from-date and --to-date for a custom run")
        return custom_window(_parse_date(args.from_date), _parse_date(args.to_date))
    return resolve_window(args.window, as_of=date.today())


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _window_payload(window) -> dict[str, object]:
    return {
        "label": window.label,
        "start": window.start.isoformat(),
        "end": window.end.isoformat(),
        "filename_part": window.filename_part(),
        "query_params": window.as_query_params(),
    }


def _redacted_settings(settings: Settings) -> dict[str, object]:
    payload = asdict(settings)
    for key in list(payload):
        if key in {"access_token", "client_id", "client_secret"} and payload[key]:
            payload[key] = "***"
    return payload
