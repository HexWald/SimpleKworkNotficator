import asyncio
import logging

from telegram import Bot
from kwork import Kwork

from .settings import load_settings
from .tracker import track_new_projects

def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

async def amain() -> None:
    settings = load_settings("config.ini")
    api = Kwork(settings.login, settings.password)
    bot = Bot(token=settings.telegram_token)

    try:
        await track_new_projects(api, bot, settings)
    finally:
        try:
            await api.close()
        except Exception:
            logging.getLogger("kwork-tracker").exception("Failed to close Kwork API session")

def main() -> None:
    setup_logging()
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        print("Stopped.")

if __name__ == "__main__":
    main()
