# Simple Kwork Notifier

A Python bot that checks selected Kwork categories and sends new projects to a Telegram group.

## How it works

Each poll processes the whole returned list, oldest project first. IDs are remembered after Telegram accepts the message. Overlapping polls and repeated IDs in the same response are skipped.

If sending fails, the failed project stays unacknowledged and can be retried on the next poll. Projects already delivered during that batch are skipped. A failed project must still be present in a later Kwork response to be retried.

The last 2048 delivered IDs are kept in memory. Restarting clears this history, so the initial batch can be sent again. A timeout after Telegram accepted a message can also cause a duplicate on retry. This is not an exactly-once delivery service.

## Setup

Use Python 3.10 or newer.

```sh
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy `config.example.ini` to `config.ini` and fill in the Kwork login, Telegram token and group ID. Keep `config.ini` out of Git.

Run from the repository root:

```sh
python -m src.kwork_notifier.main
```

## Tests

```sh
python -m unittest discover -s tests -v
```

Tests use a fake bot and API. They do not load credentials or send real messages.

## Files

- `tracker.py`: polling, delivery history and sending.
- `formatting.py`: message text and response activity labels.
- `settings.py`: configuration.
- `main.py`: application startup and logging.

MIT license.
