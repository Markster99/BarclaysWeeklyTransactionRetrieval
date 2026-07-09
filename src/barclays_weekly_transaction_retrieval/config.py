from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .exceptions import ConfigurationError


SANDBOX_BASE_URL = "https://sandbox.api.barclays:443/open-banking/v4.0/sandbox/aisp"
LIVE_BASE_URL = "https://telesto.api.barclays:443/open-banking/v4.0/aisp"


@dataclass(frozen=True)
class Settings:
    environment: str
    base_url: str
    account_ids: tuple[str, ...]
    output_dir: Path
    state_file: Path
    access_token: str | None
    token_url: str | None
    client_id: str | None
    client_secret: str | None
    client_cert_path: Path | None
    client_key_path: Path | None
    ca_bundle_path: Path | None
    timeout_seconds: float
    max_retries: int
    user_agent: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        environment = os.getenv("BARCLAYS_ENVIRONMENT", "mock").strip().lower()
        if environment not in {"mock", "sandbox", "live"}:
            raise ConfigurationError("BARCLAYS_ENVIRONMENT must be mock, sandbox or live")

        base_url = os.getenv("BARCLAYS_BASE_URL", "").strip()
        if not base_url:
            base_url = LIVE_BASE_URL if environment == "live" else SANDBOX_BASE_URL

        raw_account_ids = os.getenv("BARCLAYS_ACCOUNT_IDS", "")
        account_ids = tuple(value.strip() for value in raw_account_ids.split(",") if value.strip())

        return cls(
            environment=environment,
            base_url=base_url.rstrip("/"),
            account_ids=account_ids,
            output_dir=Path(os.getenv("BARCLAYS_OUTPUT_DIR", "data/out")),
            state_file=Path(os.getenv("BARCLAYS_STATE_FILE", "data/state/run_state.json")),
            access_token=_blank_to_none(os.getenv("BARCLAYS_ACCESS_TOKEN")),
            token_url=_blank_to_none(os.getenv("BARCLAYS_TOKEN_URL")),
            client_id=_blank_to_none(os.getenv("BARCLAYS_CLIENT_ID")),
            client_secret=_blank_to_none(os.getenv("BARCLAYS_CLIENT_SECRET")),
            client_cert_path=_optional_path("BARCLAYS_CLIENT_CERT_PATH"),
            client_key_path=_optional_path("BARCLAYS_CLIENT_KEY_PATH"),
            ca_bundle_path=_optional_path("BARCLAYS_CA_BUNDLE_PATH"),
            timeout_seconds=float(os.getenv("BARCLAYS_TIMEOUT_SECONDS", "30")),
            max_retries=int(os.getenv("BARCLAYS_MAX_RETRIES", "3")),
            user_agent=os.getenv("BARCLAYS_USER_AGENT", "BarclaysWeeklyTransactionRetrieval/0.1"),
        )

    def validate_for_network_call(self) -> None:
        if self.environment == "mock":
            return

        has_static_token = bool(self.access_token)
        has_client_credentials = bool(self.token_url and self.client_id and self.client_secret)
        if not has_static_token and not has_client_credentials:
            raise ConfigurationError(
                "Set BARCLAYS_ACCESS_TOKEN or BARCLAYS_TOKEN_URL, BARCLAYS_CLIENT_ID "
                "and BARCLAYS_CLIENT_SECRET before calling Barclays."
            )

        if self.environment == "live" and not self.client_cert_path:
            raise ConfigurationError(
                "Live mode normally requires transport certificate material. "
                "Set BARCLAYS_CLIENT_CERT_PATH or use sandbox/mock mode."
            )


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _optional_path(name: str) -> Path | None:
    value = _blank_to_none(os.getenv(name))
    return Path(value) if value else None
