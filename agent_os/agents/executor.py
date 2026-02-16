from __future__ import annotations

from agent_os.agents.base import AgentResult, BaseAgent


class ExecutorAgent(BaseAgent):
    async def run(self, task: str, context: str) -> AgentResult:
        exec_prompt = (
            "Execute the next step of the plan. "
            "Be explicit about actions taken and results. "
            "If you need a tool, respond with a JSON object: "
            '{"tool": "tool_name", "args": {...}}'
        )
        return await super().run(f"{task}\n{exec_prompt}", context)
