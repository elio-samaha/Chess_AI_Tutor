from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

import httpx

from .models import ArchiveImportRequest


class ChessComService:
    BASE_URL = "https://api.chess.com/pub"

    async def fetch_archives(self, request: ArchiveImportRequest) -> List[dict]:
        months = list(iter_months(request.from_month, request.to_month))
        games = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            for month in months:
                response = await client.get("%s/player/%s/games/%s" % (self.BASE_URL, request.username, month))
                response.raise_for_status()
                payload = response.json()
                games.extend(payload.get("games", []))
        return games


def iter_months(start: str, end: str) -> Iterable[str]:
    start_date = datetime.strptime(start, "%Y-%m")
    end_date = datetime.strptime(end, "%Y-%m")
    cursor = start_date
    while cursor <= end_date:
        yield cursor.strftime("%Y/%m")
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)
