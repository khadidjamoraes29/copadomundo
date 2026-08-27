from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import urljoin

import requests


class FootballDataClient:
    """Small client for football-data.org with free-tier friendly throttling."""

    def __init__(
        self,
        api_token: str | None = None,
        base_url: str = "https://api.football-data.org/v4",
        timeout: int = 30,
        max_calls_per_minute: int = 10,
        max_retries: int = 3,
    ) -> None:
        self.api_token = api_token or os.getenv("FOOTBALL_DATA_API_TOKEN")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.min_interval_seconds = 62.0 / max_calls_per_minute
        self._last_request_at = 0.0

        if not self.api_token:
            raise ValueError("Set FOOTBALL_DATA_API_TOKEN or pass api_token.")

    def _wait_for_slot(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        remaining = self.min_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = urljoin(f"{self.base_url}/", path.lstrip("/"))
        headers = {
            "Accept": "application/json",
            "X-Auth-Token": self.api_token,
        }

        for attempt in range(self.max_retries + 1):
            self._wait_for_slot()
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            self._last_request_at = time.monotonic()

            if response.status_code == 403:
                raise PermissionError(
                    "football-data.org returned 403 for this endpoint/filter combination. "
                    "This usually means the free-tier token does not allow that competition, "
                    "season, or data depth."
                )

            if response.status_code != 429:
                response.raise_for_status()
                return response.json()

            if attempt >= self.max_retries:
                response.raise_for_status()

            retry_after = response.headers.get("Retry-After")
            sleep_seconds = float(retry_after) if retry_after else self.min_interval_seconds * 2
            time.sleep(sleep_seconds)

        raise RuntimeError("Unreachable retry loop exit.")

    def list_competitions(self) -> Any:
        return self.get("/competitions")

    def competition_matches(
        self,
        code: str,
        season: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        stage: str | None = None,
    ) -> Any:
        params = {
            "season": season,
            "dateFrom": date_from,
            "dateTo": date_to,
            "status": status,
            "stage": stage,
        }
        params = {key: value for key, value in params.items() if value is not None}
        return self.get(f"/competitions/{code}/matches", params=params)

    def competition_teams(self, code: str, season: int | None = None) -> Any:
        params = {"season": season} if season is not None else None
        return self.get(f"/competitions/{code}/teams", params=params)
