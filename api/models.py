from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class CoinSummary(BaseModel):
    """Краткая информация о монете для таблицы на дашборде."""

    coin_id: str
    coin_name: str
    symbol: str
    close_price: Decimal
    daily_change_pct: Decimal | None
    avg_volume: int | None
    avg_market_cap: int | None
    ma_7d: Decimal | None
    ma_30d: Decimal | None

    model_config = {"from_attributes": True}


class PriceHistory(BaseModel):
    """Одна точка на графике цены: дата + OHLC + метрики."""

    price_date: date
    open_price: Decimal
    close_price: Decimal
    high_price: Decimal
    low_price: Decimal
    daily_change_pct: Decimal | None
    volatility_score: Decimal | None
    avg_volume: int | None
    ma_7d: Decimal | None
    ma_30d: Decimal | None

    model_config = {"from_attributes": True}


class NewsItem(BaseModel):
    """Одна новость с sentiment для боковой панели дашборда."""

    title: str
    description: str | None
    url: str
    source: str | None
    published_at: datetime | None
    sentiment_score: Decimal | None
    sentiment_label: str | None

    model_config = {"from_attributes": True}


class TopMover(BaseModel):
    """Монета из топа роста или падения за период."""

    coin_id: str
    coin_name: str
    symbol: str
    period: str
    close_price: Decimal | None
    change_pct: Decimal | None
    avg_volume: int | None
    mover_type: str
    rank: int

    model_config = {"from_attributes": True}
