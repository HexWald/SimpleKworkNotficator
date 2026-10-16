from __future__ import annotations

import asyncio
import logging
from collections import deque
from typing import TYPE_CHECKING

from .formatting import build_message

if TYPE_CHECKING:
    from kwork import Kwork
    from telegram import Bot
    from .settings import Settings

logger = logging.getLogger("kwork-tracker")


class DeliveryHistory:
    def __init__(self, limit: int = 2048):
        if limit < 1:
            raise ValueError("History limit must be positive")
        self.limit = limit
        self._ids = set()
        self._order = deque()

    def __contains__(self, project_id: int) -> bool:
        return project_id in self._ids

    def remember(self, project_id: int) -> None:
        if project_id in self._ids:
            return
        if len(self._order) == self.limit:
            self._ids.remove(self._order.popleft())
        self._order.append(project_id)
        self._ids.add(project_id)


async def send_new_projects(projects, bot: Bot, chat_id: int, history: DeliveryHistory) -> int:
    sent = 0
    for project in sorted(projects, key=lambda item: item.id):
        if project.id in history:
            continue

        await bot.send_message(chat_id=chat_id, text=build_message(project))
        history.remember(project.id)
        sent += 1
        logger.info("Sent project id=%s", project.id)
    return sent


async def track_new_projects(api: Kwork, bot: Bot, settings: Settings) -> None:
    history = DeliveryHistory()

    while True:
        try:
            projects = await api.get_projects(categories_ids=list(settings.categories_ids))
            if projects:
                sent = await send_new_projects(projects, bot, settings.group_chat_id, history)
                logger.info("Poll complete: received=%s sent=%s", len(projects), sent)
            else:
                logger.info("No projects found.")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Error while polling/sending")

        await asyncio.sleep(settings.poll_interval_seconds)
