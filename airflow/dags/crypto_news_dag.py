import logging
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict, cast

import psycopg
import requests
from textblob import TextBlob

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from db_utils import get_connection


logger = logging.getLogger(__name__)


class ArticleData(TypedDict, total=False):
    title:       str | None
    description: str | None
    url:         str | None
    publishedAt: str | None
    source:      dict[str, Any]
    content:     str | None


# Покрываем все монеты которые собирает CoinGecko DAG.
# Ключ — coin_id из CoinGecko, значение — ключевые слова для поиска в тексте новости.
TRACKED_COINS: dict[str, list[str]] = {
    'bitcoin':          ['bitcoin', 'btc'],
    'ethereum':         ['ethereum', 'eth'],
    'tether':           ['tether', 'usdt'],
    'binancecoin':      ['binance', 'bnb'],
    'solana':           ['solana', 'sol'],
    'ripple':           ['ripple', 'xrp'],
    'usd-coin':         ['usd coin', 'usdc'],
    'staked-ether':     ['staked ether', 'steth'],
    'dogecoin':         ['dogecoin', 'doge'],
    'cardano':          ['cardano', 'ada'],
    'tron':             ['tron', 'trx'],
    'avalanche-2':      ['avalanche', 'avax'],
    'chainlink':        ['chainlink', 'link'],
    'polkadot':         ['polkadot', 'dot'],
    'polygon':          ['polygon', 'matic'],
    'shiba-inu':        ['shiba', 'shib'],
    'litecoin':         ['litecoin', 'ltc'],
    'uniswap':          ['uniswap', 'uni'],
    'stellar':          ['stellar', 'xlm'],
    'monero':           ['monero', 'xmr'],
}

NEWSAPI_URL  = "https://newsapi.org/v2/everything"
SEARCH_QUERY = "cryptocurrency OR bitcoin OR ethereum OR crypto"


def _parse_articles(raw: Any) -> list[ArticleData]:
    if not isinstance(raw, list):
        raise ValueError(f"NewsAPI вернул неожиданный формат: {type(raw)}")
    return cast(list[ArticleData], raw)


def _compute_sentiment(title: str, description: str) -> tuple[float, str]:
    text = f"{title}. {description}".strip(". ")

    # TextBlob возвращает polarity от -1.0 до +1.0.
    # Порог ±0.1 отделяет явный позитив/негатив от нейтральных новостей.
    polarity: float = round(float(TextBlob(text).sentiment.polarity), 4)

    if polarity > 0.1:
        label = 'positive'
    elif polarity < -0.1:
        label = 'negative'
    else:
        label = 'neutral'

    return polarity, label


def _find_coin_mentions(title: str, description: str) -> list[str]:
    text = (title + " " + description).lower()
    return [
        coin_id
        for coin_id, keywords in TRACKED_COINS.items()
        if any(keyword in text for keyword in keywords)
    ]


def fetch_crypto_news() -> None:
    import os
    api_key = os.getenv('NEWSAPI_KEY')
    if not api_key:
        raise ValueError("NEWSAPI_KEY не задан в переменных окружения")

    logger.info("Начинаем сбор крипто-новостей с NewsAPI")

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
                'pageSize': 100,
                'apiKey':   api_key,
            },
            timeout=30,
        )
        response.raise_for_status()

        data     = response.json()
        articles = _parse_articles(data.get('articles', []))
        logger.info(f"Получено {len(articles)} новостей с NewsAPI")

    except requests.exceptions.Timeout:
        logger.error("NewsAPI не ответил за 30 секунд")
        raise

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к NewsAPI: {e}")
        raise

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                logger.info("Подключились к PostgreSQL, начинаем запись новостей")

                saved_count   = 0
                skipped_count = 0

                for article in articles:
                    title       = article.get('title') or ''
                    description = article.get('description') or ''
                    url         = article.get('url')
                    published   = article.get('publishedAt')

                    if not title or not url:
                        skipped_count += 1
                        continue

                    source_name   = article.get('source', {}).get('name')
                    coin_mentions = _find_coin_mentions(title, description)

                    sentiment_score, sentiment_label = _compute_sentiment(title, description)

                    published_dt: datetime | None = None
                    if published:
                        try:
                            published_dt = datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ')
                        except ValueError:
                            logger.warning(f"Не удалось распарсить дату: {published}")

                    # ON CONFLICT DO NOTHING — пропускаем дубликаты по url (UNIQUE в схеме).
                    cursor.execute("""
                        INSERT INTO raw_news
                            (title, description, url, source, published_at,
                             coin_mentions, sentiment_score, sentiment_label)
                        VALUES
                            (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO NOTHING
                    """, (
                        title,
                        description or None,
                        url,
                        source_name,
                        published_dt,
                        coin_mentions if coin_mentions else None,
                        sentiment_score,
                        sentiment_label,
                    ))

                    # rowcount = 0 если ON CONFLICT сработал (дубль), 1 если вставлено
                    if cursor.rowcount > 0:
                        saved_count += 1
                    else:
                        skipped_count += 1

                logger.info(
                    f"Обработано {len(articles)} новостей: "
                    f"сохранено {saved_count}, дублей/пропущено {skipped_count}"
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
    schedule='0 */6 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['crypto', 'news', 'newsapi'],
) as dag:

    PythonOperator(
        task_id='fetch_and_save_news',
        python_callable=fetch_crypto_news,
    )
