from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class MemoryRecord:
    id: int | None
    role: str
    content: str
    category: str
    created_at: datetime

