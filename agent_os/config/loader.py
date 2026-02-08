from __future__ import annotations

import os

from agent_os.config.settings import Settings


def load_settings() -> Settings:
    return Settings(
        base_url=os.getenv("AGENT_OS_BASE_URL", "http://127.0.0.1:1234/v1"),
        api_key=os.getenv("AGENT_OS_API_KEY", "local"),
        model=os.getenv("AGENT_OS_MODEL", "local-model"),
        embedding_model=os.getenv("AGENT_OS_EMBED_MODEL", "local-embedding"),
        telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        log_level=os.getenv("AGENT_OS_LOG_LEVEL", "INFO"),
    )
