from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx

from .auth import TokenProvider
from .config import Settings
from .dates import DateWindow
from .exceptions import BarclaysApiError


@dataclass
class BarclaysApiClient:
    settings: Settings
    token_provider: TokenProvider

    def list_accounts(self) -> list[dict[str, Any]]:
        payload = self._get("/accounts")
        return _extract_list(payload, "Account")

    def get_balances(self, account_id: str) -> list[dict[str, Any]]:
        payload = self._get(f"/accounts/{account_id}/balances")
        return _extract_list(payload, "Balance")

    def get_transactions(self, account_id: str, window: DateWindow) -> list[dict[str, Any]]:
        payload = self._get(f"/accounts/{account_id}/transactions", params=window.as_query_params())
        transactions = _extract_list(payload, "Transaction")

        next_url = _next_link(payload)
        while next_url:
            payload = self._get_absolute(next_url)
            transactions.extend(_extract_list(payload, "Transaction"))
            next_url = _next_link(payload)

        return transactions

    def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        return self._request("GET", f"{self.settings.base_url}{path}", params=params)

    def _get_absolute(self, url: str) -> dict[str, Any]:
        return self._request("GET", url, params=None)

    def _request(self, method: str, url: str, params: dict[str, str] | None) -> dict[str, Any]:
        headers = self._headers()

        verify: bool | str = True
        if self.settings.ca_bundle_path:
            verify = str(self.settings.ca_bundle_path)

        cert = None
        if self.settings.client_cert_path and self.settings.client_key_path:
            cert = (str(self.settings.client_cert_path), str(self.settings.client_key_path))

        last_error: Exception | None = None
        for attempt in range(1, self.settings.max_retries + 1):
            try:
                with httpx.Client(timeout=self.settings.timeout_seconds, cert=cert, verify=verify) as client:
                    response = client.request(method, url, params=params, headers=headers)

                if response.status_code in {408, 429, 500, 502, 503, 504}:
                    last_error = BarclaysApiError(f"Retryable HTTP {response.status_code} from {url}")
                    continue

                if response.status_code >= 400:
                    raise BarclaysApiError(f"HTTP {response.status_code} from {url}: {response.text[:300]}")

                return response.json()
            except (httpx.HTTPError, BarclaysApiError) as exc:
                last_error = exc
                if attempt >= self.settings.max_retries:
                    break

        raise BarclaysApiError(f"Request failed after retries: {last_error}")

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token_provider.get_token()}",
            "User-Agent": self.settings.user_agent,
            "x-customer-user-agent": self.settings.user_agent,
            "x-fapi-auth-date": datetime.now(timezone.utc).isoformat(),
            "x-fapi-interaction-id": str(uuid4()),
        }


def _extract_list(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    data = payload.get("Data", {})
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise BarclaysApiError(f"Expected Data.{key} to be a list")
    return [item for item in value if isinstance(item, dict)]


def _next_link(payload: dict[str, Any]) -> str | None:
    links = payload.get("Links", {})
    next_link = links.get("Next") or links.get("next")
    return str(next_link) if next_link else None
