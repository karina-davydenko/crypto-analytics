-- silver_news: серебряный слой для новостей.
--
-- Что делает этот слой:
-- 1. Дедупликация — одна запись на URL (уникальный ключ новости)
-- 2. Очистка — убираем новости без заголовка или ссылки
-- 3. Sentiment — читаем тональность вычисленную Airflow DAG через TextBlob
--    (у старых записей без sentiment подставляем 'neutral' / 0.0 через COALESCE)
--
-- Материализация: TABLE (физическая таблица для ускорения gold моделей).

with ranked as (
    select
        *,

        -- Дедупликация по url.
        -- URL — уникальный ключ новости.
        -- Если один URL попал дважды (редко, но бывает при перекрытии временных окон),
        -- оставляем только самую позднюю загрузку.
        row_number() over (
            partition by url
            order by fetched_at desc
        ) as rn

    from {{ ref('bronze_news') }}

    where
        title is not null
        and url  is not null
),

final as (
    select
        id,
        title,
        description,
        url,
        source,
        published_at,

        -- coin_mentions — массив TEXT[] с монетами упомянутыми в новости.
        -- Может быть NULL если ни одна монета не распознана.
        coin_mentions,

        -- Sentiment вычислен в Airflow DAG с помощью TextBlob.
        -- COALESCE(x, default) — возвращает x если он не NULL, иначе default.
        -- Нужен для старых записей загруженных до того как мы добавили sentiment анализ.
        coalesce(sentiment_score, 0.0)       as sentiment_score,
        coalesce(sentiment_label, 'neutral') as sentiment_label,

        fetched_at,
        _loaded_at

    from ranked
    where rn = 1
)

select * from final
