from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from .config import Settings
from .exceptions import AuthenticationError


class TokenProvider:
    def get_token(self) -> str:
        raise NotImplementedError


@dataclass
class StaticTokenProvider(TokenProvider):
    token: str

    def get_token(self) -> str:
        if not self.token:
            raise AuthenticationError("No access token configured")
        return self.token


@dataclass
class OAuthClientCredentialsProvider(TokenProvider):
    settings: Settings
    _cached_token: str | None = None
    _expires_at: float = 0

    def get_token(self) -> str:
        if self._cached_token and time.time() < self._expires_at - 60:
            return self._cached_token

        if not self.settings.token_url:
            raise AuthenticationError("BARCLAYS_TOKEN_URL is not configured")
        if not self.settings.client_id or not self.settings.client_secret:
            raise AuthenticationError("Client ID and client secret are required")

        cert = None
        if self.settings.client_cert_path and self.settings.client_key_path:
            cert = (str(self.settings.client_cert_path), str(self.settings.client_key_path))

        verify: bool | str = True
        if self.settings.ca_bundle_path:
            verify = str(self.settings.ca_bundle_path)

        response = httpx.post(
            self.settings.token_url,
            data={"grant_type": "client_credentials"},
            auth=(self.settings.client_id, self.settings.client_secret),
            cert=cert,
            verify=verify,
            timeout=self.settings.timeout_seconds,
        )
        if response.status_code >= 400:
            raise AuthenticationError(f"Token request failed with HTTP {response.status_code}")

        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise AuthenticationError("Token response did not include access_token")

        self._cached_token = str(token)
        self._expires_at = time.time() + int(payload.get("expires_in", 300))
        return self._cached_token


def build_token_provider(settings: Settings) -> TokenProvider:
    if settings.access_token:
        return StaticTokenProvider(settings.access_token)
    return OAuthClientCredentialsProvider(settings)
