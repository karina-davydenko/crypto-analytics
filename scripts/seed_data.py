"""
seed_data.py — заполняет PostgreSQL реальными историческими данными с CoinGecko.

Запуск:
    pip install requests psycopg
    python scripts/seed_data.py --database-url "postgresql://user:pass@host/db"

CoinGecko free API не требует ключа, но ограничен ~10-30 запросов в минуту.
Скрипт добавляет паузы между запросами чтобы не получить 429.
"""

import argparse
import logging
import time
from datetime import datetime, timezone

import psycopg
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Топ 10 монет — достаточно для красивого дашборда
COINS = [
    ("bitcoin",   "Bitcoin",   "btc"),
    ("ethereum",  "Ethereum",  "eth"),
    ("tether",    "Tether",    "usdt"),
    ("solana",    "Solana",    "sol"),
    ("ripple",    "XRP",       "xrp"),
    ("dogecoin",  "Dogecoin",  "doge"),
    ("cardano",   "Cardano",   "ada"),
    ("chainlink", "Chainlink", "link"),
    ("polkadot",  "Polkadot",  "dot"),
    ("litecoin",  "Litecoin",  "ltc"),
]

COINGECKO_URL = "https://api.coingecko.com/api/v3"

# Задержка между запросами — защита от rate limit (30 req/min на free tier)
REQUEST_DELAY_SEC = 3


def fetch_market_chart(coin_id: str, days: int = 30) -> dict:
    """
    Запрашивает исторические данные по монете за последние N дней.
    Возвращает словарь с ключами: prices, market_caps, total_volumes.
    Каждый элемент — список пар [timestamp_ms, value].
    """
    url = f"{COINGECKO_URL}/coins/{coin_id}/market_chart"
    response = requests.get(
        url,
        params={"vs_currency": "usd", "days": days},
        timeout=30,
        headers={"Accept": "application/json"},
    )

    # 429 = rate limit — ждём и пробуем ещё раз
    if response.status_code == 429:
        logger.warning("Rate limit от CoinGecko, ждём 60 секунд...")
        time.sleep(60)
        response = requests.get(url, params={"vs_currency": "usd", "days": days}, timeout=30)

    response.raise_for_status()
    return response.json()


def insert_prices(
    cursor: psycopg.Cursor,
    coin_id: str,
    coin_name: str,
    symbol: str,
    data: dict,
) -> int:
    """
    Вставляет исторические цены в raw_prices.
    Возвращает количество вставленных строк.
    """
    prices       = data.get("prices", [])
    market_caps  = data.get("market_caps", [])
    volumes      = data.get("total_volumes", [])

    # Совмещаем три массива по индексу — они всегда одной длины
    rows = []
    for i, (ts_ms, price) in enumerate(prices):
        # CoinGecko отдаёт timestamp в миллисекундах → конвертируем в datetime
        fetched_at = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)

        market_cap = int(market_caps[i][1]) if i < len(market_caps) else None
        volume     = int(volumes[i][1])     if i < len(volumes)      else None

        rows.append((
            coin_id,
            coin_name,
            symbol.upper(),
            round(price, 8),
            market_cap,
            volume,
            None,       # price_change_24h — нет в этом эндпоинте
            fetched_at,
        ))

    # executemany вставляет все строки одним батчем — быстрее чем в цикле
    cursor.executemany("""
        INSERT INTO raw_prices
            (coin_id, coin_name, symbol, price_usd,
             market_cap, volume_24h, price_change_24h, fetched_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, rows)

    return len(rows)


def main(database_url: str, days: int) -> None:
    logger.info(f"Подключаемся к БД: {database_url[:40]}...")

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            total_inserted = 0

            for coin_id, coin_name, symbol in COINS:
                logger.info(f"Загружаем данные для {coin_name} ({coin_id})...")

                try:
                    data = fetch_market_chart(coin_id, days)
                    count = insert_prices(cursor, coin_id, coin_name, symbol, data)
                    conn.commit()
                    total_inserted += count
                    logger.info(f"  ✓ {coin_name}: вставлено {count} записей")

                except requests.HTTPError as e:
                    logger.error(f"  ✗ {coin_name}: HTTP ошибка {e}")
                    conn.rollback()

                except Exception as e:
                    logger.error(f"  ✗ {coin_name}: {e}")
                    conn.rollback()

                # Пауза между монетами чтобы не попасть под rate limit
                time.sleep(REQUEST_DELAY_SEC)

            logger.info(f"\nГотово! Всего вставлено {total_inserted} записей в raw_prices.")
            logger.info("Теперь запусти: dbt run")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed crypto price data from CoinGecko")
    parser.add_argument(
        "--database-url",
        required=True,
        help='PostgreSQL URL, например: postgresql://user:pass@host:5432/db',
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Количество дней истории (по умолчанию 30)",
    )
    args = parser.parse_args()
    main(args.database_url, args.days)
