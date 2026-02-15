import asyncio
import configparser
import html
import logging
import re
from typing import Optional, Sequence

from kwork import Kwork
from telegram import Bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("kwork-tracker")

config = configparser.ConfigParser(interpolation=None)
config.read("config.ini")

GROUP_CHAT_ID = int(config.get("Credentials", "GROUP_ID"))
TELEGRAM_TOKEN = config.get("Credentials", "TELEGRAM_TOKEN")
LOGIN = config.get("Credentials", "LOGIN")
PASSWORD = config.get("Credentials", "PASSWORD")

CATEGORIES_IDS: Sequence[int] = [41, 80, 40, 255, 81]
POLL_INTERVAL_SECONDS = 60


_BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)


def clean_text(text: str) -> str:
    """Convert simple HTML-ish text from API into readable plain text."""
    if not text:
        return ""
    text = _BR_RE.sub("\n", text)
    text = html.unescape(text)
    return text.strip()


def offers_label(offers: int) -> str:
    if offers < 5:
        return " ( Actual! )"
    if offers <= 10:
        return " ( 50/50 actual :/ )"
    return " ( Maybe not actual :( )"


def build_message(project) -> str:
    title = clean_text(project.title)
    description = clean_text(project.description)

    return (
        "New Project:\n"
        f"Title: {title}, Price: {project.price}₽\n"
        f"Description: {description}\n"
        f"Responses: {project.offers}{offers_label(project.offers)}\n"
        f"Link: https://kwork.ru/projects/{project.id}/view"
    )


async def fetch_latest_project(api: Kwork):
    projects = await api.get_projects(categories_ids=list(CATEGORIES_IDS))
    if not projects:
        return None
    return projects[0]


async def track_new_projects(api: Kwork, bot: Bot) -> None:
    last_project_id: Optional[int] = None

    while True:
        try:
            latest = await fetch_latest_project(api)

            if latest is None:
                logger.info("No projects found. Sleeping...")
            else:
                if last_project_id is None:
                    # На старте просто запоминаем (и по желанию можно отправить сразу)
                    last_project_id = latest.id
                    msg = build_message(latest)
                    await bot.send_message(chat_id=GROUP_CHAT_ID, text=msg)
                    logger.info("Sent initial project id=%s", latest.id)
                elif latest.id != last_project_id:
                    last_project_id = latest.id
                    msg = build_message(latest)
                    await bot.send_message(chat_id=GROUP_CHAT_ID, text=msg)
                    logger.info("Sent new project id=%s", latest.id)
                else:
                    logger.debug("No new projects. Latest id=%s", latest.id)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception("Error while polling/sending: %s", e)

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def main() -> None:
    api = Kwork(LOGIN, PASSWORD)
    bot = Bot(token=TELEGRAM_TOKEN)

    try:
        await track_new_projects(api, bot)
    finally:
        # гарантированно закрываем даже при Ctrl+C/ошибках
        try:
            await api.close()
        except Exception:
            logger.exception("Failed to close Kwork API session!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped.")
