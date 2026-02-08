from __future__ import annotations

import argparse
import asyncio

from agent_os.config.loader import load_settings
from agent_os.core.llm import LLMClient
from agent_os.core.logging import configure_logging, get_logger
from agent_os.interfaces.telegram import TelegramInterface
from agent_os.memory.manager import MemoryManager
from agent_os.memory.store import SQLiteMemoryStore
from agent_os.swarm.controller import SwarmController
from agent_os.swarm.operator import AutonomousOperator
from agent_os.tools.ops import ToolRunner


async def run_swarm() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    log = get_logger("agent_os.main")

    llm = LLMClient(settings.base_url, settings.api_key, settings.model, settings.embedding_model)
    store = SQLiteMemoryStore(settings.storage_path)
    memory = MemoryManager(store, llm)
    tools = ToolRunner()
    controller = SwarmController(
        llm=llm,
        memory=memory,
        tools=tools,
        max_iterations=settings.max_iterations,
        retry_limit=settings.retry_limit,
        retry_backoff_s=settings.retry_backoff_s,
    )

    operator = AutonomousOperator(controller, interval_s=settings.operator_interval_s)

    parser = argparse.ArgumentParser(description="Agent-OS Swarm")
    parser.add_argument("--operator", action="store_true", help="Run autonomous operator mode")
    args = parser.parse_args()

    if args.operator:
        log.info("Starting autonomous operator mode")
        operator.schedule_goal("Review recent tasks and continue unfinished work.")
        await operator.start()
        return

    telegram = TelegramInterface(settings.telegram_token)
    log.info("Listening for Telegram messages")
    tasks: set[asyncio.Task] = set()
    async for message in telegram.listen():
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        if not text:
            continue
        task = asyncio.create_task(_handle_message(controller, telegram, chat_id, text, log))
        tasks.add(task)
        task.add_done_callback(tasks.discard)


def main() -> None:
    asyncio.run(run_swarm())


async def _handle_message(controller: SwarmController, telegram: TelegramInterface, chat_id: int, text: str, log) -> None:
    try:
        result = await controller.handle_task(text)
        await telegram.send_message(chat_id, result.response)
    except Exception as exc:  # noqa: BLE001
        log.error("Failed to handle message: %s", exc)
        await telegram.send_message(chat_id, f"Error: {exc}")


if __name__ == "__main__":
    main()
