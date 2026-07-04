from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import urljoin

import requests


class TransfermarktClient:
    """Small configurable client for Transfermarkt-compatible APIs."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 30,
        sleep_seconds: float = 1.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("TRANSFERMARKT_API_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("TRANSFERMARKT_API_KEY")
        self.timeout = timeout
        self.sleep_seconds = sleep_seconds

        if not self.base_url:
            raise ValueError("Set TRANSFERMARKT_API_BASE_URL or pass base_url.")

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = urljoin(f"{self.base_url}/", path.lstrip("/"))
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
        response.raise_for_status()
        time.sleep(self.sleep_seconds)
        return response.json()

    def search_club(self, query: str) -> Any:
        return self.get("/clubs/search", {"query": query})

    def club_squad(self, club_id: str, season_id: str | int) -> Any:
        return self.get(f"/clubs/{club_id}/squad", {"season_id": season_id})

