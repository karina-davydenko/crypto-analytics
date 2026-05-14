-- bronze_news: бронзовый слой для новостей о криптовалютах.

select
    -- Первичный ключ
    id,

    -- Заголовок новости
    title,

    -- Описание новости (может быть NULL если источник не предоставил)
    description,

    -- URL статьи — уникальный ключ, защищает от дублей
    url,

    -- Название источника (CoinDesk, Reuters и т.д.)
    source,

    -- Время публикации на сайте источника
    published_at,

    -- Массив монет упомянутых в новости.
    -- PostgreSQL тип TEXT[] — массив строк.
    -- Пример: {'bitcoin', 'ethereum'}
    -- NULL если монеты не обнаружены в тексте.
    coin_mentions,

    -- Время загрузки с NewsAPI нашим DAG-ом
    fetched_at,

    -- Тональность новости вычисленная Airflow DAG через TextBlob.
    -- Значение от -1.0 (негатив) до +1.0 (позитив). NULL у старых записей.
    sentiment_score,

    -- Текстовая метка: 'positive', 'negative', 'neutral'. NULL у старых записей.
    sentiment_label,

    -- Когда dbt последний раз обновлял этот слой
    current_timestamp as _loaded_at

from {{ source('public', 'raw_news') }}
