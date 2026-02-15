import configparser
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    group_chat_id: int
    telegram_token: str
    login: str
    password: str

    categories_ids: tuple[int, ...] = (41, 80, 40, 255, 81)
    poll_interval_seconds: int = 60

def load_settings(config_path: str = "config.ini") -> Settings:
    p = Path(config_path)
    if not p.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}. "
            f"Create it based on config.example.ini"
        )

    config = configparser.ConfigParser(interpolation=None)
    config.read(config_path)

    return Settings(
        group_chat_id=int(config.get("Credentials", "GROUP_ID")),
        telegram_token=config.get("Credentials", "TELEGRAM_TOKEN"),
        login=config.get("Credentials", "LOGIN"),
        password=config.get("Credentials", "PASSWORD"),
    )
