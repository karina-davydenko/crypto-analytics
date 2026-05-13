import logging
import os
from datetime import datetime, timedelta
from typing import Any, TypedDict, cast

import psycopg
import requests

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator


logger = logging.getLogger(__name__)

class CoinData(TypedDict, total=False):
    id:                             str
    name:                           str
    symbol:                         str
    current_price:                  float | None
    market_cap:                     int | None
    total_volume:                   int | None
    price_change_percentage_24h:    float | None

def _build_conninfo() -> str:
    host     = os.getenv('POSTGRES_HOST', 'postgres')
    port     = os.getenv('POSTGRES_PORT', '5432')
    dbname   = os.getenv('POSTGRES_DB', 'crypto_analytics')
    user     = os.getenv('POSTGRES_USER', 'airflow')
    password = os.getenv('POSTGRES_PASSWORD', 'airflow')
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd"
    "&order=market_cap_desc"
    "&per_page=50"
    "&page=1"
    "&sparkline=false"
    "&price_change_percentage=24h"
)


def _parse_coins(raw: Any) -> list[CoinData]:
    if not isinstance(raw, list):
        raise ValueError(f"CoinGecko вернул неожиданный формат: {type(raw)}")
    return cast(list[CoinData], raw)


def fetch_crypto_prices() -> None:
    logger.info("Начинаем сбор цен криптовалют с CoinGecko API")

    try:
        response = requests.get(COINGECKO_URL, timeout=30)
        response.raise_for_status()
        coins = _parse_coins(response.json())
        logger.info(f"Получено {len(coins)} монет с CoinGecko API")

    except requests.exceptions.Timeout:
        logger.error("CoinGecko API не ответил за 30 секунд")
        raise

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к CoinGecko API: {e}")
        raise

    try:
        with psycopg.connect(_build_conninfo()) as conn:
            with conn.cursor() as cursor:
                logger.info("Подключились к PostgreSQL, начинаем запись данных")

                saved_count = 0

                for coin in coins:
                    coin_id   = coin.get('id')
                    coin_name = coin.get('name')

                    if not coin_id or not coin_name:
                        logger.warning(f"Пропускаем монету без ID или названия: {coin}")
                        continue

                    cursor.execute("""
                        INSERT INTO raw_prices
                            (coin_id, coin_name, symbol, price_usd, market_cap, volume_24h, price_change_24h)
                        VALUES
                            (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        coin_id,
                        coin_name,
                        coin.get('symbol', '').upper(),
                        coin.get('current_price'),
                        coin.get('market_cap'),
                        coin.get('total_volume'),
                        coin.get('price_change_percentage_24h'),
                    ))

                    saved_count += 1

                logger.info(f"Успешно сохранено {saved_count} монет в raw_prices")

    except psycopg.Error as e:
        logger.error(f"Ошибка PostgreSQL: {e}")
        raise


default_args = {
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
    'email_on_retry': False,
}


with DAG(
    dag_id='crypto_prices_dag',
    default_args=default_args,
    description='Сбор цен топ 50 криптовалют с CoinGecko каждый час',
    schedule='@hourly',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['crypto', 'prices', 'coingecko'],
) as dag:

    PythonOperator(
        task_id='fetch_and_save_prices',
        python_callable=fetch_crypto_prices,
    )
