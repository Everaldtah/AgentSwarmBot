from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from typing import Deque

from agent_os.core.logging import get_logger
from agent_os.swarm.controller import SwarmController, SwarmResult


@dataclass(slots=True)
class ScheduledGoal:
    goal: str


class AutonomousOperator:
    def __init__(self, controller: SwarmController, interval_s: int = 15) -> None:
        self._controller = controller
        self._interval_s = interval_s
        self._queue: Deque[ScheduledGoal] = deque()
        self._running = False
        self._log = get_logger("agent_os.operator")

    def schedule_goal(self, goal: str) -> None:
        self._queue.append(ScheduledGoal(goal=goal))
        self._log.info("Scheduled goal: %s", goal)

    async def start(self) -> None:
        self._running = True
        while self._running:
            if self._queue:
                goal = self._queue.popleft()
                await self._handle_goal(goal.goal)
            await asyncio.sleep(self._interval_s)

    async def stop(self) -> None:
        self._running = False

    async def _handle_goal(self, goal: str) -> SwarmResult | None:
        self._log.info("Handling goal: %s", goal)
        try:
            return await self._controller.handle_task(goal)
        except Exception as exc:  # noqa: BLE001
            self._log.error("Autonomous operator failed: %s", exc)
            return None
