from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_os.core.llm import LLMClient, LLMResponse
from agent_os.core.logging import get_logger
from agent_os.memory.manager import MemoryManager
from agent_os.tools.ops import ToolRunner


@dataclass(slots=True)
class AgentResult:
    content: str
    raw: dict[str, Any]


class BaseAgent:
    def __init__(
        self,
        name: str,
        llm: LLMClient,
        memory: MemoryManager,
        tools: ToolRunner,
    ) -> None:
        self.name = name
        self._llm = llm
        self._memory = memory
        self._tools = tools
        self._log = get_logger(f"agent_os.agent.{name}")

    async def run(self, task: str, context: str) -> AgentResult:
        messages = [
            {"role": "system", "content": f"You are the {self.name} agent."},
            {"role": "user", "content": f"Task: {task}\nContext:\n{context}"},
        ]
        response: LLMResponse = await self._llm.chat(messages)
        await self._memory.remember(self.name, response.content, "agent_output")
        return AgentResult(content=response.content, raw=response.raw)
