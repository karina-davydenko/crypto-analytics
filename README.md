# Crypto Analytics Platform

End-to-end data pipeline for cryptocurrency market analysis — from raw API data to an interactive React dashboard.

![CI](https://github.com/karina-davydenko/crypto-analytics/actions/workflows/ci.yml/badge.svg)

---

## Overview

The platform collects real-time price data for the top 50 cryptocurrencies and crypto news, processes it through a multi-layer data pipeline, and exposes the results via a REST API consumed by a React dashboard.

**Key features:**

- Hourly price ingestion from CoinGecko (no API key required)
- News sentiment analysis with TextBlob (positive / neutral / negative)
- 7-day and 30-day moving averages, volatility score, top gainers/losers
- Interactive dashboard with price charts, news feed, and sentiment visualization

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Data Sources                        │
│         CoinGecko API          NewsAPI                  │
└────────────────┬───────────────────┬────────────────────┘
                 │                   │
                 ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│              Apache Airflow (orchestration)             │
│   crypto_prices_dag (every 1h)  crypto_news_dag (6h)   │
└────────────────┬───────────────────┬────────────────────┘
                 │                   │
                 ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                   PostgreSQL                            │
│         raw_prices            raw_news                  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  dbt (transformations)                  │
│                                                         │
│  Bronze  →  silver_prices      silver_news              │
│             (clean, dedup)     (+ sentiment score)      │
│                                                         │
│  Gold    →  gold_coin_daily    gold_top_movers          │
│             (MA7, MA30,        (top 10 gainers/losers   │
│              volatility)        per 24h / 7d / 30d)     │
│                                                         │
│          →  gold_coin_news_correlation                  │
│             (price vs sentiment lag analysis)           │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI (REST API)                    │
│  GET /coins                  GET /top-gainers           │
│  GET /coins/{id}/history     GET /top-losers            │
│  GET /coins/{id}/news        GET /health/db             │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              React Dashboard (TypeScript)               │
│  Coins table  │  Price chart (Recharts)                 │
│  Period filter│  News list with sentiment               │
│  24h / 7d / 30d            Sentiment bar chart          │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer            | Technology                                 |
| ---------------- | ------------------------------------------ |
| Orchestration    | Apache Airflow 3 (CeleryExecutor)          |
| Database         | PostgreSQL 15                              |
| Transformations  | dbt (window functions, CTEs)               |
| API              | FastAPI + psycopg3 (async connection pool) |
| Frontend         | React 19 + TypeScript + Recharts           |
| Containerization | Docker + docker compose                    |
| CI               | GitHub Actions                             |

---

## dbt Models

The transformation layer follows the **Medallion architecture** (Bronze → Silver → Gold):

| Model                        | Description                                               |
| ---------------------------- | --------------------------------------------------------- |
| `bronze_prices`              | 1:1 with `raw_prices`, typed view                         |
| `bronze_news`                | 1:1 with `raw_news`, typed view                           |
| `silver_prices`              | Deduplication, null filtering, type casting               |
| `silver_news`                | + sentiment score and label via TextBlob                  |
| `gold_coin_daily`            | OHLC per day, MA7, MA30, volatility score, daily change % |
| `gold_top_movers`            | Top 10 gainers and losers per 24h / 7d / 30d              |
| `gold_coin_news_correlation` | Price vs sentiment lag correlation per coin per day       |

Highlights: `FIRST_VALUE`, `LAG`, `ROW_NUMBER`, `AVG OVER`, `ROWS BETWEEN` window functions.

---

## Getting Started

### Prerequisites

- Docker + docker compose
- Python 3.12+ (for FastAPI local dev)
- Node.js 20+ (for frontend local dev)
- [NewsAPI key](https://newsapi.org) (free tier)

### 1. Clone and configure

```bash
git clone https://github.com/karina-davydenko/crypto-analytics.git
cd crypto-analytics
cp .env.example .env
```

Edit `.env` and fill in your values:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Start infrastructure

```bash
docker compose up -d
```

| Service    | URL                                   |
| ---------- | ------------------------------------- |
| Airflow UI | http://localhost:8080 (admin / admin) |
| pgAdmin    | http://localhost:5050                 |
| PostgreSQL | localhost:5433                        |

### 3. Run dbt transformations

```bash
cd dbt
dbt run
dbt test
```

### 4. Start FastAPI

```bash
cd api
python -m venv .venv-api && source .venv-api/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 5. Start React dashboard

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

---

## Project Structure

```
crypto-analytics/
├── .github/workflows/ci.yml   # GitHub Actions: ruff + tsc + eslint + build
├── docker-compose.yml          # Airflow + PostgreSQL + Redis + pgAdmin
├── .env.example                # Environment variable template
├── airflow/
│   ├── dags/
│   │   ├── db_utils.py         # Shared DB connection utility
│   │   ├── crypto_prices_dag.py  # CoinGecko → raw_prices (every 1h)
│   │   └── crypto_news_dag.py    # NewsAPI → raw_news (every 6h)
│   └── init.sql                # DB schema: raw_prices, raw_news
├── dbt/
│   └── models/
│       ├── bronze/             # Typed views over raw tables
│       ├── silver/             # Cleaned + enriched data
│       └── gold/               # Aggregated, analytics-ready
├── api/
│   ├── main.py                 # FastAPI endpoints
│   ├── database.py             # Connection pool (psycopg3)
│   ├── models.py               # Pydantic response models
│   └── settings.py             # Pydantic settings from .env
└── frontend/
    └── src/
        ├── App.tsx             # Layout, state, API calls
        └── components/
            ├── CoinsTable.tsx  # Sortable, searchable coins table
            ├── CoinDetail.tsx  # Price chart + news for selected coin
            ├── PriceChart.tsx  # Recharts line chart (MA7, MA30)
            ├── SentimentChart.tsx  # Daily sentiment bar chart
            ├── NewsList.tsx    # News feed with sentiment labels
            └── PeriodFilter.tsx    # 24h / 7d / 30d segmented control
```

---

## CI Pipeline

GitHub Actions runs on every push to `main`:

1. **Python lint** — `ruff check api/ airflow/dags/`
2. **TypeScript type check** — `tsc --noEmit`
3. **ESLint** — `npm run lint`
4. **Frontend build** — `npm run build`
