from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4

from .auth import build_token_provider
from .client import BarclaysApiClient
from .config import Settings
from .dates import DateWindow
from .exporters import ExportResult, ExportWriter
from .mock_api import MockBarclaysApiClient
from .normalise import map_transaction
from .state import RunState


class AccountTransactionClient(Protocol):
    def list_accounts(self) -> list[dict[str, Any]]:
        ...

    def get_transactions(self, account_id: str, window: DateWindow) -> list[dict[str, Any]]:
        ...


@dataclass(frozen=True)
class PipelineResult:
    run_id: str
    requested_accounts: list[str]
    fetched_rows: int
    exported_rows: int
    skipped_duplicate_count: int
    export: ExportResult


class WeeklyTransactionPipeline:
    def __init__(self, settings: Settings, use_mock: bool = False) -> None:
        self.settings = settings
        self.use_mock = use_mock or settings.environment == "mock"
        self.client: AccountTransactionClient

        if self.use_mock:
            self.client = MockBarclaysApiClient()
        else:
            settings.validate_for_network_call()
            self.client = BarclaysApiClient(settings, build_token_provider(settings))

        self.state = RunState.load(settings.state_file)
        self.exporter = ExportWriter(settings.output_dir)

    def run(self, window: DateWindow) -> PipelineResult:
        run_id = uuid4().hex[:12]
        account_ids = self._resolve_account_ids()

        exported_rows = []
        skipped_duplicates = 0

        for account_id in account_ids:
            raw_transactions = self.client.get_transactions(account_id, window)
            for raw in raw_transactions:
                row = map_transaction(run_id, account_id, raw)
                if self.state.is_seen(row.idempotency_key):
                    skipped_duplicates += 1
                    continue
                exported_rows.append(row)

        self.state.mark_seen([row.idempotency_key for row in exported_rows])
        self.state.save()

        export = self.exporter.write(
            run_id=run_id,
            window=window,
            rows=exported_rows,
            requested_accounts=account_ids,
            skipped_duplicate_count=skipped_duplicates,
        )

        return PipelineResult(
            run_id=run_id,
            requested_accounts=account_ids,
            fetched_rows=len(exported_rows) + skipped_duplicates,
            exported_rows=len(exported_rows),
            skipped_duplicate_count=skipped_duplicates,
            export=export,
        )

    def _resolve_account_ids(self) -> list[str]:
        if self.settings.account_ids:
            return list(self.settings.account_ids)

        accounts = self.client.list_accounts()
        return [str(account["AccountId"]) for account in accounts if account.get("AccountId")]
