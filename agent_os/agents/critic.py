from __future__ import annotations

from agent_os.agents.base import AgentResult, BaseAgent


class CriticAgent(BaseAgent):
    async def run(self, task: str, context: str) -> AgentResult:
        critique_prompt = (
            "Evaluate the execution result. "
            "Identify issues, missing steps, or confirm success."
        )
        return await super().run(f"{task}\n{critique_prompt}", context)
