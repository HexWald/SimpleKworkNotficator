import asyncio
import logging
from typing import Optional

from telegram import Bot
from kwork import Kwork

from .formatting import build_message
from .settings import Settings

logger = logging.getLogger("kwork-tracker")

async def fetch_latest_project(api: Kwork, settings: Settings):
    projects = await api.get_projects(categories_ids=list(settings.categories_ids))
    if not projects:
        return None
    return projects[0]

async def track_new_projects(api: Kwork, bot: Bot, settings: Settings) -> None:
    last_project_id: Optional[int] = None

    while True:
        try:
            latest = await fetch_latest_project(api, settings)

            if latest is None:
                logger.info("No projects found.")
            else:
                if last_project_id is None:
                    last_project_id = latest.id
                    await bot.send_message(chat_id=settings.group_chat_id, text=build_message(latest))
                    logger.info("Sent initial project id=%s", latest.id)

                elif latest.id != last_project_id:
                    last_project_id = latest.id
                    await bot.send_message(chat_id=settings.group_chat_id, text=build_message(latest))
                    logger.info("Sent new project id=%s", latest.id)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception("Error while polling/sending: %s", e)

        await asyncio.sleep(settings.poll_interval_seconds)
