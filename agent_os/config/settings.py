from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    base_url: str = "http://127.0.0.1:1234/v1"
    api_key: str = "local"
    model: str = "local-model"
    embedding_model: str = "local-embedding"
    telegram_token: str = ""
    storage_path: Path = Path("data/agent_os.sqlite3")
    log_level: str = "INFO"
    max_iterations: int = 8
    retry_limit: int = 3
    retry_backoff_s: float = 0.8
    operator_interval_s: int = 15


DEFAULT_SETTINGS = Settings()
