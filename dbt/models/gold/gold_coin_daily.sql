-- gold_coin_daily: агрегированные дневные данные по каждой монете.
--
-- Что делает этот слой:
-- 1. Группирует почасовые цены по дням
-- 2. Вычисляет цену открытия, закрытия, максимум, минимум за день
-- 3. Считает скользящее среднее 7 и 30 дней (window functions)
-- 4. Считает volatility — насколько сильно цена колебалась за день
--
with daily_prices as (
    select
        coin_id,
        coin_name,
        symbol,
        -- Это "ключ" для группировки — все записи одного дня объединяются в одну строку.
        date_trunc('day', price_hour)::date as price_date,
        -- Цена открытия = самая ранняя цена за день
        first_value(price_usd) over (
            partition by coin_id, date_trunc('day', price_hour)
            order by price_hour asc
            rows between unbounded preceding and unbounded following
        ) as open_price,

        -- Цена закрытия = самая поздняя цена за день
        first_value(price_usd) over (
            partition by coin_id, date_trunc('day', price_hour)
            order by price_hour desc
            rows between unbounded preceding and unbounded following
        ) as close_price,

        -- Максимальная и минимальная цена за день
        max(price_usd) over (
            partition by coin_id, date_trunc('day', price_hour)
        ) as high_price,

        min(price_usd) over (
            partition by coin_id, date_trunc('day', price_hour)
        ) as low_price,

        -- Средний объём торгов за день
        avg(volume_24h) over (
            partition by coin_id, date_trunc('day', price_hour)
        ) as avg_volume,

        -- Средняя рыночная капитализация за день
        avg(market_cap) over (
            partition by coin_id, date_trunc('day', price_hour)
        ) as avg_market_cap,

        price_usd,
        price_hour

    from {{ ref('silver_prices') }}
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by coin_id, price_date
            order by price_hour desc
        ) as rn
    from daily_prices
),

daily_agg as (
    select
        coin_id,
        coin_name,
        symbol,
        price_date,
        open_price,
        close_price,
        high_price,
        low_price,
        avg_volume::bigint    as avg_volume,
        avg_market_cap::bigint as avg_market_cap,

        -- Изменение цены за день в процентах.
        round(
            (close_price - open_price) / nullif(open_price, 0) * 100,
            2
        ) as daily_change_pct,

        -- Volatility score — насколько сильно цена колебалась внутри дня.
        round(
            (high_price - low_price) / nullif(low_price, 0) * 100,
            2
        ) as volatility_score

    from deduplicated
    where rn = 1
),

final as (
    select
        coin_id,
        coin_name,
        symbol,
        price_date,
        open_price,
        close_price,
        high_price,
        low_price,
        daily_change_pct,
        volatility_score,
        avg_volume,
        avg_market_cap,

        -- Скользящее среднее за 7 дней (MA7).
        -- AVG(...) OVER (...) — оконная функция, не группирует строки, а считает по окну.
        -- ROWS BETWEEN 6 PRECEDING AND CURRENT ROW = текущий день + 6 предыдущих = 7 дней.
        -- Сортировка по дате гарантирует правильный порядок.
        round(
            avg(close_price) over (
                partition by coin_id
                order by price_date asc
                rows between 6 preceding and current row
            ),
            8
        ) as ma_7d,

        -- Скользящее среднее за 30 дней (MA30).
        round(
            avg(close_price) over (
                partition by coin_id
                order by price_date asc
                rows between 29 preceding and current row
            ),
            8
        ) as ma_30d,

        -- Процентное изменение цены закрытия относительно предыдущего дня.
        round(
            (close_price - lag(close_price, 1) over (
                partition by coin_id
                order by price_date asc
            )) / nullif(lag(close_price, 1) over (
                partition by coin_id
                order by price_date asc
            ), 0) * 100,
            2
        ) as price_change_vs_prev_day

    from daily_agg
)

select * from final
order by coin_id, price_date
