from __future__ import annotations

import asyncio
import logging
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING

from .formatting import build_message

if TYPE_CHECKING:
    from kwork import Kwork
    from telegram import Bot
    from .settings import Settings

logger = logging.getLogger("kwork-tracker")


class DeliveryHistory:
    def __init__(self, limit: int = 2048, *, path: Path | None = None, chat_id: int = 0):
        if limit < 1:
            raise ValueError("History limit must be positive")
        self.limit = limit
        self._chat_id = chat_id
        self._db = sqlite3.connect(path if path is not None else ":memory:")
        try:
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS deliveries (
                    sequence INTEGER PRIMARY KEY,
                    chat_id INTEGER NOT NULL,
                    project_id INTEGER NOT NULL,
                    UNIQUE (chat_id, project_id)
                )
            """)
        except sqlite3.Error:
            self.close()
            raise

    def __contains__(self, project_id: int) -> bool:
        return self._db.execute(
            "SELECT 1 FROM deliveries WHERE chat_id = ? AND project_id = ?",
            (self._chat_id, project_id),
        ).fetchone() is not None

    def remember(self, project_id: int) -> None:
        with self._db:
            self._db.execute("""
                INSERT INTO deliveries (chat_id, project_id) VALUES (?, ?)
                ON CONFLICT (chat_id, project_id) DO NOTHING
            """, (self._chat_id, project_id))
            self._db.execute("""
                DELETE FROM deliveries WHERE chat_id = ? AND sequence <= (
                    SELECT sequence FROM deliveries WHERE chat_id = ?
                    ORDER BY sequence DESC LIMIT 1 OFFSET ?
                )
            """, (self._chat_id, self._chat_id, self.limit))

    def close(self) -> None:
        self._db.close()


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
    with closing(DeliveryHistory(path=settings.history_path, chat_id=settings.group_chat_id)) as history:
        while True:
            try:
                projects = await api.get_projects(categories_ids=list(settings.categories_ids))
                if projects:
                    sent = await send_new_projects(projects, bot, settings.group_chat_id, history)
                    logger.info("Poll complete: received=%s sent=%s", len(projects), sent)
                else:
                    logger.info("No projects found.")
            except (asyncio.CancelledError, sqlite3.Error):
                raise
            except Exception:
                logger.exception("Error while polling/sending")

            await asyncio.sleep(settings.poll_interval_seconds)
