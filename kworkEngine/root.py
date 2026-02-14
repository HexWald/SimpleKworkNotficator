import asyncio
import configparser
import html
import logging
import json
from pathlib import Path

from kwork import Kwork
from telegram import Bot

logging.basicConfig(level=logging.INFO)

config = configparser.ConfigParser(interpolation=None)
config.read("config.ini")

GROUP_CHAT_ID = int(config.get("Credentials", "GROUP_ID"))
TELEGRAM_TOKEN = config.get("Credentials", "TELEGRAM_TOKEN")
LOGIN = config.get("Credentials", "LOGIN")
PASSWORD = config.get("Credentials", "PASSWORD")

CATEGORIES_IDS = [41, 80, 40, 255, 81]
POLL_INTERVAL_SECONDS = 60

STATE_FILE = Path("state.json")


def clean_text(text: str) -> str:
    """Convert basic HTML formatting/entities into plain text."""
    if not text:
        return ""
    text = text.replace("<br>", "\n")
    return html.unescape(text)


def offers_label(offers_count: int) -> str:
    if offers_count < 5:
        return " ( Actual! )"
    if offers_count <= 10:
        return " ( 50/50 actual :/ )"
    return " ( Maybe not actual :( )"


def load_last_seen_project_id() -> int | None:
    if not STATE_FILE.exists():
        return None
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        value = data.get("last_seen_project_id")
        return int(value) if value is not None else None
    except Exception:
        return None


def save_last_seen_project_id(project_id: int) -> None:
    STATE_FILE.write_text(
        json.dumps({"last_seen_project_id": project_id}, ensure_ascii=False),
        encoding="utf-8",
    )


async def send_project_to_telegram(telegram_bot: Bot, project) -> None:
    title = clean_text(getattr(project, "title", ""))
    description = clean_text(getattr(project, "description", ""))

    # Prevent Telegram "message too long" errors (safe-ish cap)
    if len(description) > 2500:
        description = description[:2500] + "…"

    offers = int(getattr(project, "offers", 0))
    price = getattr(project, "price", "")
    project_id = getattr(project, "id", "")

    message = (
        "New Project:\n"
        f"Title: {title}\n"
        f"Price: {price}₽\n"
        f"Description:\n{description}\n\n"
        f"Responses: {offers}{offers_label(offers)}\n"
        f"Link: https://kwork.ru/projects/{project_id}/view"
    )

    await telegram_bot.send_message(chat_id=GROUP_CHAT_ID, text=message)


async def poll_new_projects(kwork_api: Kwork, telegram_bot: Bot) -> None:
    last_seen_project_id = load_last_seen_project_id()

    # Initialize state without sending (avoid spam on restarts)
    if last_seen_project_id is None:
        projects = await kwork_api.get_projects(categories_ids=CATEGORIES_IDS)
        if projects:
            last_seen_project_id = projects[0].id
            save_last_seen_project_id(last_seen_project_id)
            logging.info("Initialized last_seen_project_id=%s", last_seen_project_id)

    backoff = POLL_INTERVAL_SECONDS

    while True:
        try:
            projects = await kwork_api.get_projects(categories_ids=CATEGORIES_IDS)

            if projects:
                # projects assumed sorted newest -> oldest
                unseen_projects = []
                for project in projects:
                    if project.id == last_seen_project_id:
                        break
                    unseen_projects.append(project)

                # send in chronological order (oldest unseen -> newest)
                for project in reversed(unseen_projects):
                    await send_project_to_telegram(telegram_bot, project)
                    last_seen_project_id = project.id
                    save_last_seen_project_id(last_seen_project_id)

            backoff = POLL_INTERVAL_SECONDS
        except Exception as exc:
            logging.exception("Polling error: %s", exc)
            backoff = min(backoff * 2, 300)  # exponential backoff up to 5 min

        await asyncio.sleep(backoff)


async def main() -> None:
    kwork_api = Kwork(LOGIN, PASSWORD)
    telegram_bot = Bot(token=TELEGRAM_TOKEN)

    try:
        await poll_new_projects(kwork_api, telegram_bot)
    finally:
        await kwork_api.close()


if __name__ == "__main__":
    asyncio.run(main())
