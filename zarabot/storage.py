from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .detector import StockStatus


@dataclass(frozen=True)
class ProductState:
    url: str
    status: StockStatus
    title: str | None


class StateStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.database_path)
        self._connection.row_factory = sqlite3.Row
        self._migrate()

    def close(self) -> None:
        self._connection.close()

    def get(self, url: str) -> ProductState | None:
        row = self._connection.execute(
            "select url, status, title from product_states where url = ?",
            (url,),
        ).fetchone()
        if row is None:
            return None
        return ProductState(url=row["url"], status=StockStatus(row["status"]), title=row["title"])

    def upsert(self, url: str, status: StockStatus, title: str | None) -> None:
        now = datetime.now(UTC).isoformat()
        self._connection.execute(
            """
            insert into product_states (url, status, title, updated_at)
            values (?, ?, ?, ?)
            on conflict(url) do update set
                status = excluded.status,
                title = coalesce(excluded.title, product_states.title),
                updated_at = excluded.updated_at
            """,
            (url, status.value, title, now),
        )
        self._connection.commit()

    def _migrate(self) -> None:
        self._connection.execute(
            """
            create table if not exists product_states (
                url text primary key,
                status text not null,
                title text,
                updated_at text not null
            )
            """
        )
        self._connection.commit()
