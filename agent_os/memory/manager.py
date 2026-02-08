from __future__ import annotations

from datetime import datetime

from agent_os.core.llm import LLMClient
from agent_os.core.logging import get_logger
from agent_os.memory.models import MemoryRecord
from agent_os.memory.store import SQLiteMemoryStore
from agent_os.memory.vector_index import top_k_similar


class MemoryManager:
    def __init__(self, store: SQLiteMemoryStore, llm: LLMClient) -> None:
        self._store = store
        self._llm = llm
        self._log = get_logger("agent_os.memory")

    async def remember(self, role: str, content: str, category: str) -> int:
        record = MemoryRecord(
            id=None,
            role=role,
            content=content,
            category=category,
            created_at=datetime.utcnow(),
        )
        record_id = self._store.add_record(record)
        try:
            embedding = await self._llm.embed([content])
            self._store.add_embedding(record_id, embedding[0])
        except Exception as exc:  # noqa: BLE001
            self._log.error("Embedding failed: %s", exc)
        return record_id

    async def recall(self, query: str, limit: int = 5) -> list[MemoryRecord]:
        try:
            embedding = await self._llm.embed([query])
        except Exception as exc:  # noqa: BLE001
            self._log.error("Embedding recall failed: %s", exc)
            return []
        matches = top_k_similar(embedding[0], self._store.fetch_all_embeddings(), k=limit)
        results = []
        for record_id, _score in matches:
            record = self._store.fetch_record_by_id(record_id)
            if record:
                results.append(record)
        return results
