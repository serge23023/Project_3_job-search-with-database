import os
from typing import Any
from dotenv import load_dotenv


def load_config() -> dict[str, Any]:
    """Загружает конфигурацию подключения к БД из .env файла.

    Returns:
        dict[str, Any]: словарь с параметрами подключения
                        (host, port, user, password).
    """
    load_dotenv()

    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }
