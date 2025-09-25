import requests
import psycopg2
from src.config import load_config


def fetch_currency_rates() -> dict[str, float]:
    """Получает курсы валют из API hh.ru."""
    url = "https://api.hh.ru/dictionaries"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    result = {}
    for item in data["currency"]:
        code = item["code"]
        if code == "RUR":
            code = "RUB"
        rate = float(item["rate"]) if "rate" in item and item["rate"] else 1.0
        result[code] = rate

    return result


def update_currency_rates():
    """Сохраняет актуальные курсы валют в БД."""
    rates = fetch_currency_rates()
    config = load_config()
    conn = psycopg2.connect(
        dbname="hh_db",
        user=config["user"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
    )
    cur = conn.cursor()

    for code, rate in rates.items():
        cur.execute(
            """
            INSERT INTO currency_rates (code, rate)
            VALUES (%s, %s)
            ON CONFLICT (code) DO UPDATE SET rate = EXCLUDED.rate
        """,
            (code, rate),
        )

    conn.commit()
    cur.close()
    conn.close()
    print("💱 Курсы валют обновлены")
