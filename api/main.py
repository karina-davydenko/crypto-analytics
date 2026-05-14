# main.py — FastAPI приложение с эндпоинтами для крипто-дашборда.
#
# Как запустить:
#   source .venv-api/bin/activate
#   uvicorn main:app --reload --port 8000
#
# Swagger: http://localhost:8000/docs

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Literal

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg.rows import DictRow

from database import close_pool, get_cursor, init_pool
from models import CoinSummary, NewsItem, PriceHistory, TopMover
from settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

Cursor = Annotated[psycopg.Cursor[DictRow], Depends(get_cursor)]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Запуск API — инициализация пула соединений...")
    init_pool()
    yield
    logger.info("Остановка API — закрытие пула соединений.")
    close_pool()


app = FastAPI(
    title="Crypto Analytics API",
    description="API для дашборда криптовалютной аналитики. Данные из PostgreSQL через dbt.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(psycopg.Error)
async def db_exception_handler(request: Request, exc: psycopg.Error) -> JSONResponse:
    logger.error("Ошибка БД на %s: %s", request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "Ошибка при получении данных"})



@app.get("/coins", response_model=list[CoinSummary])
def get_coins(cur: Cursor) -> list[CoinSummary]:
    """Список монет для таблицы на главной странице дашборда."""
    cur.execute("""
        SELECT DISTINCT ON (coin_id)
            coin_id, coin_name, symbol, close_price,
            daily_change_pct, avg_volume, avg_market_cap, ma_7d, ma_30d
        FROM gold_coin_daily
        ORDER BY coin_id, price_date DESC
    """)
    return [CoinSummary(**row) for row in cur.fetchall()]


@app.get("/coins/{coin_id}/history", response_model=list[PriceHistory])
def get_coin_history(
    coin_id: str,
    cur: Cursor,
    days: int = Query(default=7, ge=1, le=365, description="Количество дней (1-365)"),
) -> list[PriceHistory]:
    """История цен монеты для графика."""
    cur.execute("""
        SELECT
            price_date, open_price, close_price, high_price, low_price,
            daily_change_pct, volatility_score, avg_volume, ma_7d, ma_30d
        FROM gold_coin_daily
        WHERE coin_id = %s
          AND price_date >= CURRENT_DATE - (%s * INTERVAL '1 day')
        ORDER BY price_date ASC
    """, (coin_id, days))

    rows = cur.fetchall()
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Монета '{coin_id}' не найдена или нет данных за {days} дней",
        )
    return [PriceHistory(**row) for row in rows]


@app.get("/coins/{coin_id}/news", response_model=list[NewsItem])
def get_coin_news(
    coin_id: str,
    cur: Cursor,
    days: int = Query(default=7, ge=1, le=90, description="Количество дней (1-90)"),
) -> list[NewsItem]:
    """Новости по монете для списка и графика sentiment."""
    cur.execute("""
        SELECT
            title, description, url, source, published_at,
            sentiment_score, sentiment_label
        FROM silver_news
        WHERE %s = ANY(coin_mentions)
          AND published_at >= NOW() - (%s * INTERVAL '1 day')
        ORDER BY published_at DESC
        LIMIT 100
    """, (coin_id, days))
    return [NewsItem(**row) for row in cur.fetchall()]


@app.get("/top-gainers", response_model=list[TopMover])
def get_top_gainers(
    cur: Cursor,
    period: Literal["24h", "7d", "30d"] = Query(default="24h"),
) -> list[TopMover]:
    """Топ 10 монет с наибольшим ростом за период."""
    cur.execute("""
        SELECT coin_id, coin_name, symbol, period,
               close_price, change_pct, avg_volume, mover_type, rank
        FROM gold_top_movers
        WHERE period = %s AND mover_type = 'gainer'
        ORDER BY rank ASC
    """, (period,))
    return [TopMover(**row) for row in cur.fetchall()]


@app.get("/top-losers", response_model=list[TopMover])
def get_top_losers(
    cur: Cursor,
    period: Literal["24h", "7d", "30d"] = Query(default="24h"),
) -> list[TopMover]:
    """Топ 10 монет с наибольшим падением за период."""
    cur.execute("""
        SELECT coin_id, coin_name, symbol, period,
               close_price, change_pct, avg_volume, mover_type, rank
        FROM gold_top_movers
        WHERE period = %s AND mover_type = 'loser'
        ORDER BY rank ASC
    """, (period,))
    return [TopMover(**row) for row in cur.fetchall()]


@app.get("/health")
def health_check(cur: Cursor) -> dict[str, str]:
    """Проверяет что API и соединение с БД работают."""
    cur.execute("SELECT 1")
    return {"status": "ok", "database": "connected"}
