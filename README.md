# Simple Kwork Notifier

Checks selected Kwork categories and posts new projects to a Telegram group.

## Setup

Use Python 3.12 or newer.

```sh
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy `config.example.ini` to `config.ini` and fill in your Kwork login and password, Telegram bot token and group ID. Run the bot from the repository root.

```sh
python -m src.kwork_notifier.main
```

## Delivery

The bot checks Kwork every minute and sends older projects first. It keeps the last 2048 confirmed IDs per Telegram group in `deliveries.sqlite3` next to `config.ini`. Keep the database when updating the bot. An empty database means the bot sends the projects in the first poll.

If a send fails, the bot can retry it when the project appears in another poll. Telegram can accept a message just before the connection times out, so a retry may send it twice. Long messages are shortened to fit Telegram's limit and still include the project link.

## Tests

```sh
python -m unittest discover -s tests -v
```

Tests use a fake Telegram bot and Kwork API.
