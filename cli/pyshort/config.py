import configparser
from pathlib import Path

CONFIG_PATH = Path.home() / ".pyshortrc"
DEFAULT_API_URL = "http://localhost:8000"


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    if CONFIG_PATH.exists():
        config.read(CONFIG_PATH)
    return config


def get_api_url() -> str:
    config = load_config()
    return config.get("default", "api_url", fallback=DEFAULT_API_URL)


def save_api_url(api_url: str) -> None:
    config = load_config()
    if "default" not in config:
        config["default"] = {}
    config["default"]["api_url"] = api_url
    with open(CONFIG_PATH, "w") as f:
        config.write(f)
