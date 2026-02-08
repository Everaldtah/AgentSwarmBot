from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from agent_os.agents.critic import CriticAgent
from agent_os.agents.executor import ExecutorAgent
from agent_os.agents.planner import PlannerAgent
from agent_os.core.llm import LLMClient
from agent_os.core.logging import get_logger
from agent_os.memory.manager import MemoryManager
from agent_os.tools.ops import ToolRunner


@dataclass(slots=True)
class SwarmResult:
    response: str
    diagnostics: dict[str, Any]


class SwarmController:
    def __init__(
        self,
        llm: LLMClient,
        memory: MemoryManager,
        tools: ToolRunner,
        max_iterations: int,
        retry_limit: int,
        retry_backoff_s: float,
    ) -> None:
        self._llm = llm
        self._memory = memory
        self._tools = tools
        self._max_iterations = max_iterations
        self._retry_limit = retry_limit
        self._retry_backoff_s = retry_backoff_s
        self._log = get_logger("agent_os.swarm")
        self._planner = PlannerAgent("planner", llm, memory, tools)
        self._executor = ExecutorAgent("executor", llm, memory, tools)
        self._critic = CriticAgent("critic", llm, memory, tools)

    async def handle_task(self, task: str) -> SwarmResult:
        await self._memory.remember("user", task, "conversation")
        recall = await self._memory.recall(task, limit=3)
        context = "\n".join(f"{item.role}: {item.content}" for item in recall)
        plan = await self._run_with_retries(self._planner.run, task, context)
        await self._memory.remember("planner", plan.content, "plan")

        execution_context = f"Plan:\n{plan.content}\n\nMemory:\n{context}"
        execution_result = ""
        critique_result = ""
        for iteration in range(1, self._max_iterations + 1):
            self._log.info("Iteration %s", iteration)
            try:
                executor = await self._run_with_retries(
                    self._executor.run,
                    task,
                    execution_context,
                )
                execution_result = await self._handle_tool_calls(executor.content)
                await self._memory.remember("executor", execution_result, "execution")
            except Exception as exc:  # noqa: BLE001
                self._log.error("Executor failed: %s", exc)
                await self._memory.remember("system", f"Executor failed: {exc}", "diagnostic")
                break

            critique = await self._run_with_retries(
                self._critic.run,
                task,
                f"{execution_context}\n\nExecution:\n{execution_result}",
            )
            critique_result = critique.content
            await self._memory.remember("critic", critique_result, "critique")
            await self._memory.remember("system", critique_result, "self_reflection")
            if "success" in critique_result.lower():
                break
            execution_context = f"Plan:\n{plan.content}\n\nCritique:\n{critique_result}"

        await self._memory.remember("system", "Task completed", "status")
        return SwarmResult(
            response=execution_result or "Task completed with no execution output.",
            diagnostics={
                "plan": plan.content,
                "critique": critique_result,
            },
        )

    async def _run_with_retries(self, fn, task: str, context: str):
        attempt = 0
        while True:
            try:
                return await fn(task, context)
            except Exception as exc:  # noqa: BLE001
                attempt += 1
                self._log.error("Agent error: %s", exc)
                if attempt >= self._retry_limit:
                    raise
                await asyncio.sleep(self._retry_backoff_s * attempt)

    async def _handle_tool_calls(self, content: str) -> str:
        if not content.strip().startswith("{"):
            return content
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return content
        tool_name = payload.get("tool")
        args = payload.get("args", {})
        if not tool_name:
            return content
        try:
            result = await self._dispatch_tool(tool_name, args)
        except Exception as exc:  # noqa: BLE001
            await self._memory.remember("system", f"Tool call failed: {exc}", "diagnostic")
            return f"Tool call failed: {exc}"
        return f"Tool {tool_name} result:\n{result}"

    async def _dispatch_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        match tool_name:
            case "read_file":
                return await self._tools.read_file(args["path"])
            case "write_file":
                await self._tools.write_file(args["path"], args["content"])
                return "ok"
            case "run_python":
                return await self._tools.run_python(args["code"])
            case "call_local_api":
                return await self._tools.call_local_api(args["url"], args.get("payload", {}))
            case "search_local":
                return await self._tools.search_local(args["root"], args["query"], args.get("limit", 10))
            case _:
                raise ValueError(f"Unknown tool: {tool_name}")
