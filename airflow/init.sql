-- Метаданные Airflow хранятся в БД 'airflow' 
CREATE DATABASE crypto_analytics;

\c crypto_analytics

-- Таблица raw_prices — сырые данные о ценах криптовалют.
CREATE TABLE IF NOT EXISTS raw_prices (
    id                SERIAL PRIMARY KEY,

    -- Внутренний ID монеты в CoinGecko 
    coin_id           VARCHAR(100) NOT NULL,

    -- Полное название монеты (например 'Bitcoin', 'Ethereum')
    coin_name         VARCHAR(200) NOT NULL,

    -- Тикер/символ монеты (например 'BTC', 'ETH')
    symbol            VARCHAR(20)  NOT NULL,

    -- Цена в долларах США.
    price_usd         NUMERIC(20, 8),

    -- Рыночная капитализация = цена × количество монет в обращении
    market_cap        BIGINT,

    -- Объём торгов за последние 24 часа в долларах
    volume_24h        BIGINT,

    -- Изменение цены за 24 часа в процентах (может быть отрицательным)
    price_change_24h  NUMERIC(10, 4),

    -- Время когда мы получили эти данные с API.
    fetched_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_prices_coin_id    ON raw_prices (coin_id);
CREATE INDEX IF NOT EXISTS idx_raw_prices_fetched_at ON raw_prices (fetched_at);

-- Таблица raw_news — сырые данные о новостях по криптовалютам.
CREATE TABLE IF NOT EXISTS raw_news (
    id              SERIAL PRIMARY KEY,

    -- Заголовок новости
    title           TEXT NOT NULL,

    -- Описание
    description     TEXT,

    -- Ссылка на оригинальную статью
    url             TEXT UNIQUE,

    -- Название источника (например 'CoinDesk', 'Reuters')
    source          VARCHAR(200),

    -- Время публикации новости на сайте источника
    published_at    TIMESTAMP WITH TIME ZONE,

    -- Какие монеты упомянуты в новости.
    coin_mentions   TEXT[],

    -- Время когда мы скачали эту новость с NewsAPI
    fetched_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Тональность новости — вычисляется Airflow DAG через TextBlob.
    -- Значение от -1.0 (очень негативная) до +1.0 (очень позитивная).
    sentiment_score NUMERIC(5, 4),

    -- Текстовая метка тональности: 'positive', 'negative', 'neutral'
    sentiment_label VARCHAR(10)
);

CREATE INDEX IF NOT EXISTS idx_raw_news_published_at ON raw_news (published_at);
CREATE INDEX IF NOT EXISTS idx_raw_news_coin_mentions ON raw_news USING GIN (coin_mentions);
