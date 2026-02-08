from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import aiohttp

from agent_os.core.logging import get_logger


class ToolError(RuntimeError):
    pass


class ToolRunner:
    def __init__(self) -> None:
        self._log = get_logger("agent_os.tools")

    async def read_file(self, path: str) -> str:
        file_path = Path(path)
        if not file_path.exists():
            raise ToolError(f"File not found: {path}")
        return file_path.read_text(encoding="utf-8")

    async def write_file(self, path: str, content: str) -> None:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    async def run_python(self, code: str, timeout_s: int = 10) -> str:
        process = await asyncio.create_subprocess_exec(
            "python",
            "-c",
            code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_s)
        except asyncio.TimeoutError as exc:
            process.kill()
            raise ToolError("Python execution timed out") from exc
        if process.returncode != 0:
            raise ToolError(stderr.decode("utf-8", errors="ignore"))
        return stdout.decode("utf-8", errors="ignore").strip()

    async def call_local_api(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status >= 400:
                    raise ToolError(f"API error: {response.status}")
                return await response.json()

    async def search_local(self, root: str, query: str, limit: int = 10) -> list[str]:
        cmd = ["rg", "--max-count", str(limit), query, root]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode not in (0, 1):
            raise ToolError(stderr.decode("utf-8", errors="ignore"))
        results = stdout.decode("utf-8", errors="ignore").strip().splitlines()
        return results
