from __future__ import annotations

from agent_os.agents.base import AgentResult, BaseAgent


class PlannerAgent(BaseAgent):
    async def run(self, task: str, context: str) -> AgentResult:
        plan_prompt = (
            "Create a concise step-by-step plan for the task. "
            "Return numbered steps and any tool usage hints."
        )
        return await super().run(f"{task}\n{plan_prompt}", context)
