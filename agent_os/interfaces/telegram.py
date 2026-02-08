from __future__ import annotations

import asyncio
from typing import AsyncIterator

import aiohttp

from agent_os.core.logging import get_logger


class TelegramInterface:
    def __init__(self, token: str) -> None:
        self._token = token
        self._log = get_logger("agent_os.telegram")
        self._base_url = f"https://api.telegram.org/bot{token}"
        self._offset = 0

    async def listen(self) -> AsyncIterator[dict]:
        if not self._token:
            raise RuntimeError("Telegram token is required.")
        while True:
            updates = await self._get_updates()
            for update in updates:
                self._offset = max(self._offset, update["update_id"] + 1)
                if "message" in update:
                    yield update["message"]
            await asyncio.sleep(0.2)

    async def _get_updates(self) -> list[dict]:
        payload = {"timeout": 20, "offset": self._offset}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self._base_url}/getUpdates", json=payload) as response:
                if response.status >= 400:
                    self._log.error("Telegram update error: %s", response.status)
                    return []
                data = await response.json()
                return data.get("result", [])

    async def send_message(self, chat_id: int, text: str) -> None:
        payload = {"chat_id": chat_id, "text": text}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self._base_url}/sendMessage", json=payload) as response:
                if response.status >= 400:
                    self._log.error("Telegram send error: %s", response.status)
