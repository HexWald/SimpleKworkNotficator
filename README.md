# 📦 Simple Kwork Notifier

Telegram bot that monitors new projects on Kwork and sends notifications
to a Telegram group chat.

------------------------------------------------------------------------

## 🚀 Features

-   Tracks latest Kwork projects by category
-   Sends formatted notifications to Telegram
-   Async polling
-   Clean modular project structure
-   Config-based credentials
-   Logging support

------------------------------------------------------------------------

## 🏗 Project Structure

    .
    ├── src/
    │   └── kwork_notifier/
    │       ├── __init__.py
    │       ├── main.py
    │       ├── tracker.py
    │       ├── formatting.py
    │       └── settings.py
    ├── config.example.ini
    ├── requirements.txt
    └── README.md

------------------------------------------------------------------------

## ⚙️ Installation

### 1️⃣ Clone repository

    git clone https://github.com/HexWald/SimpleKworkNotficator.git
    cd SimpleKworkNotficator

### 2️⃣ Create virtual environment

    python -m venv .venv
    source .venv/bin/activate

### 3️⃣ Install dependencies

    pip install -r requirements.txt

------------------------------------------------------------------------

## 🔑 Configuration

Create `config.ini` based on `config.example.ini`:

    [Credentials]
    GROUP_ID = -100XXXXXXXXXX
    TELEGRAM_TOKEN = your_telegram_bot_token
    LOGIN = your_kwork_login
    PASSWORD = your_kwork_password

⚠️ `config.ini` must NOT be committed to the repository.

------------------------------------------------------------------------

## ▶️ Run

From project root:

    python -m src.kwork_notifier.main

Or if using **main** entrypoint:

    python -m kwork_notifier

------------------------------------------------------------------------

## 🧠 How It Works

-   Polls Kwork API every 60 seconds
-   Compares latest project ID
-   Sends notification if a new project appears
-   Formats HTML-like description text
-   Adds response activity label

------------------------------------------------------------------------

## 🛡 Security Notice

Never commit:

-   config.ini
-   API tokens
-   passwords

If credentials were exposed, revoke them immediately.

------------------------------------------------------------------------

## 📄 License

MIT
