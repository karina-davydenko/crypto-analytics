-- silver_prices: серебряный слой для цен криптовалют.
--
-- Что делает этот слой:
-- 1. Дедупликация — одна запись на монету за каждый час (window function ROW_NUMBER)
-- 2. Очистка — убираем строки с нулевой или отсутствующей ценой
-- 3. Обогащение — добавляем поле price_hour для удобной группировки в gold слое
--
-- Материализация: TABLE (в отличие от bronze VIEW).
-- Silver хранит очищенные данные физически — это ускоряет gold модели.

with ranked as (
    select
        *,

        -- ROW_NUMBER — оконная функция (window function).
        -- Как она работает:
        --   PARTITION BY coin_id, date_trunc('hour', fetched_at)
        --     → делит все строки на группы: одна группа = одна монета за один час
        --   ORDER BY fetched_at DESC
        --     → внутри группы нумерует от новейшей к старейшей
        --   Результат: у самой свежей записи в каждой группе rn = 1
        row_number() over (
            partition by coin_id, date_trunc('hour', fetched_at)
            order by fetched_at desc
        ) as rn

    from {{ ref('bronze_prices') }}

    where
        -- Убираем записи без цены — они бесполезны для аналитики
        price_usd is not null

        -- Убираем физически невозможные цены (баг API или тестовые данные)
        and price_usd > 0
),

final as (
    select
        id,
        coin_id,
        coin_name,
        symbol,

        -- Явно указываем типы — downstream модели (gold) делают математику с этими полями.
        -- Без явного cast PostgreSQL иногда выбирает неожиданный тип при JOIN-ах.
        price_usd::numeric(20, 8)        as price_usd,
        market_cap::bigint               as market_cap,
        volume_24h::bigint               as volume_24h,
        price_change_24h::numeric(10, 4) as price_change_24h,

        fetched_at,

        -- price_hour — "канонический" timestamp для этой записи.
        -- date_trunc('hour', ...) обрезает минуты и секунды: 14:37:22 → 14:00:00
        -- Используется в gold слое для group by по времени без лишних дублей.
        date_trunc('hour', fetched_at)::timestamp with time zone as price_hour,

        _loaded_at

    from ranked

    -- Оставляем только по одной записи из каждой группы (самую свежую)
    where rn = 1
)

select * from final
