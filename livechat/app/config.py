import yaml
import os

_config = None
CONFIG_PATH = os.environ.get("LIVECHAT_CONFIG", "./config.yml")


def get_config() -> dict:
    global _config
    if _config is None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f)
    return _config


def reload_config():
    global _config
    _config = None
    return get_config()
