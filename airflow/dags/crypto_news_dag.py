import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict, cast

import psycopg
import requests

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator


logger = logging.getLogger(__name__)


# Структура одной новости из NewsAPI
class ArticleData(TypedDict, total=False):
    title:       str | None
    description: str | None
    url:         str | None
    publishedAt: str | None
    source:      dict[str, Any]
    content:     str | None


# Монеты которые ищем в новостях — совпадает с тем что собираем в raw_prices
TRACKED_COINS = {
    'bitcoin':  ['bitcoin', 'btc'],
    'ethereum': ['ethereum', 'eth'],
    'solana':   ['solana', 'sol'],
    'ripple':   ['ripple', 'xrp'],
    'cardano':  ['cardano', 'ada'],
}

NEWSAPI_URL = "https://newsapi.org/v2/everything"

# Ключевые слова для поиска крипто-новостей
SEARCH_QUERY = "cryptocurrency OR bitcoin OR ethereum OR crypto"


def _build_conninfo() -> str:
    host     = os.getenv('POSTGRES_HOST', 'postgres')
    port     = os.getenv('POSTGRES_PORT', '5432')
    dbname   = os.getenv('POSTGRES_DB', 'crypto_analytics')
    user     = os.getenv('POSTGRES_USER', 'airflow')
    password = os.getenv('POSTGRES_PASSWORD', 'airflow')
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"


def _parse_articles(raw: Any) -> list[ArticleData]:
    if not isinstance(raw, list):
        raise ValueError(f"NewsAPI вернул неожиданный формат: {type(raw)}")
    return cast(list[ArticleData], raw)


def _find_coin_mentions(title: str, description: str) -> list[str]:
    # Ищем упоминания монет в заголовке и описании новости.
    # Возвращаем список coin_id (например ['bitcoin', 'ethereum']).
    text = (title + " " + description).lower()
    mentioned = [
        coin_id
        for coin_id, keywords in TRACKED_COINS.items()
        if any(keyword in text for keyword in keywords)
    ]
    return mentioned


def fetch_crypto_news() -> None:
    api_key = os.getenv('NEWSAPI_KEY')
    if not api_key:
        raise ValueError("NEWSAPI_KEY не задан в переменных окружения")

    logger.info("Начинаем сбор крипто-новостей с NewsAPI")

    # NewsAPI бесплатный план позволяет получать новости за последние 24 часа.
    # Запрашиваем новости за последние 6 часов — соответствует расписанию DAG-а.
    from_time = (datetime.now(timezone.utc) - timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%S')

    try:
        response = requests.get(
            NEWSAPI_URL,
            params={
                'q':        SEARCH_QUERY,
                'from':     from_time,
                'sortBy':   'publishedAt',
                'language': 'en',
                'pageSize': 100,   # максимум на бесплатном плане
                'apiKey':   api_key,
            },
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        articles = _parse_articles(data.get('articles', []))

        logger.info(f"Получено {len(articles)} новостей с NewsAPI")

    except requests.exceptions.Timeout:
        logger.error("NewsAPI не ответил за 30 секунд")
        raise

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к NewsAPI: {e}")
        raise

    try:
        with psycopg.connect(_build_conninfo()) as conn:
            with conn.cursor() as cursor:
                logger.info("Подключились к PostgreSQL, начинаем запись новостей")

                saved_count   = 0
                skipped_count = 0

                for article in articles:
                    title       = article.get('title') or ''
                    description = article.get('description') or ''
                    url         = article.get('url')
                    published   = article.get('publishedAt')

                    # Пропускаем новости без заголовка или ссылки
                    if not title or not url:
                        skipped_count += 1
                        continue

                    source_name   = article.get('source', {}).get('name')
                    coin_mentions = _find_coin_mentions(title, description)

                    # Конвертируем строку ISO 8601 в datetime для PostgreSQL.
                    # NewsAPI возвращает формат: "2024-01-15T10:30:00Z"
                    published_dt: datetime | None = None
                    if published:
                        try:
                            published_dt = datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ')
                        except ValueError:
                            logger.warning(f"Не удалось распарсить дату: {published}")

                    # ON CONFLICT DO NOTHING — пропускаем дубликаты по url (UNIQUE в схеме).
                    # Это важно: если DAG запустится дважды, данные не задублируются.
                    cursor.execute("""
                        INSERT INTO raw_news
                            (title, description, url, source, published_at, coin_mentions)
                        VALUES
                            (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO NOTHING
                    """, (
                        title,
                        description or None,
                        url,
                        source_name,
                        published_dt,
                        coin_mentions if coin_mentions else None,
                    ))

                    saved_count += 1

                logger.info(
                    f"Обработано {len(articles)} новостей: "
                    f"сохранено {saved_count}, пропущено {skipped_count}"
                )

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
    dag_id='crypto_news_dag',
    default_args=default_args,
    description='Сбор крипто-новостей с NewsAPI каждые 6 часов',
    schedule='0 */6 * * *',   # каждые 6 часов: 00:00, 06:00, 12:00, 18:00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['crypto', 'news', 'newsapi'],
) as dag:

    PythonOperator(
        task_id='fetch_and_save_news',
        python_callable=fetch_crypto_news,
    )
