from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

from agent_os.memory.models import MemoryRecord


class SQLiteMemoryStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._path)
        self._connection.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                record_id INTEGER PRIMARY KEY,
                embedding TEXT NOT NULL,
                FOREIGN KEY(record_id) REFERENCES memory_records(id)
            )
            """
        )
        self._connection.commit()

    def add_record(self, record: MemoryRecord) -> int:
        cursor = self._connection.execute(
            "INSERT INTO memory_records (role, content, category, created_at) VALUES (?, ?, ?, ?)",
            (record.role, record.content, record.category, record.created_at.isoformat()),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    def add_embedding(self, record_id: int, embedding: list[float]) -> None:
        self._connection.execute(
            "INSERT OR REPLACE INTO embeddings (record_id, embedding) VALUES (?, ?)",
            (record_id, ",".join(map(str, embedding))),
        )
        self._connection.commit()

    def fetch_records(self, limit: int = 50) -> list[MemoryRecord]:
        cursor = self._connection.execute(
            "SELECT id, role, content, category, created_at FROM memory_records ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [self._row_to_record(row) for row in cursor.fetchall()]

    def fetch_all_embeddings(self) -> list[tuple[int, list[float]]]:
        cursor = self._connection.execute("SELECT record_id, embedding FROM embeddings")
        results: list[tuple[int, list[float]]] = []
        for row in cursor.fetchall():
            embedding = [float(value) for value in row["embedding"].split(",") if value]
            results.append((int(row["record_id"]), embedding))
        return results

    def fetch_record_by_id(self, record_id: int) -> MemoryRecord | None:
        cursor = self._connection.execute(
            "SELECT id, role, content, category, created_at FROM memory_records WHERE id = ?",
            (record_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def close(self) -> None:
        self._connection.close()

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            id=int(row["id"]),
            role=row["role"],
            content=row["content"],
            category=row["category"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def export_records(self) -> Iterable[dict]:
        for record in self.fetch_records(limit=500):
            yield asdict(record)
