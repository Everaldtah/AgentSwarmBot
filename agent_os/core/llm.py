from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Iterable

import aiohttp

from agent_os.core.logging import get_logger


@dataclass(slots=True)
class LLMResponse:
    content: str
    raw: dict[str, Any]


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str, embedding_model: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._embedding_model = embedding_model or model
        self._log = get_logger("agent_os.llm")

    async def chat(self, messages: Iterable[dict[str, str]], timeout_s: int = 60) -> LLMResponse:
        url = f"{self._base_url}/chat/completions"
        payload = {"model": self._model, "messages": list(messages)}
        headers = {"Authorization": f"Bearer {self._api_key}"}
        self._log.debug("LLM chat request: %s", payload)
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout_s)) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
        content = data["choices"][0]["message"]["content"]
        return LLMResponse(content=content, raw=data)

    async def embed(self, texts: list[str], timeout_s: int = 60) -> list[list[float]]:
        url = f"{self._base_url}/embeddings"
        payload = {"model": self._embedding_model, "input": texts}
        headers = {"Authorization": f"Bearer {self._api_key}"}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout_s)) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
        return [item["embedding"] for item in data["data"]]

    async def safe_chat(self, messages: Iterable[dict[str, str]], retries: int, backoff_s: float) -> LLMResponse:
        attempt = 0
        while True:
            try:
                return await self.chat(messages)
            except Exception as exc:  # noqa: BLE001
                attempt += 1
                self._log.error("LLM chat failed: %s", exc)
                if attempt >= retries:
                    raise
                await asyncio.sleep(backoff_s * attempt)
