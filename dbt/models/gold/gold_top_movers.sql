-- gold_top_movers: топ 10 монет с наибольшим ростом и падением.
--
-- Читает из gold_coin_daily и ранжирует монеты по изменению цены.
-- Три периода: 24ч (последний день), 7д, 30д.
-- Используется API эндпоинтами /top-gainers и /top-losers.

with latest_date as (
    select max(price_date) as max_date
    from {{ ref('gold_coin_daily') }}
),

-- Данные за последний день (24ч)
period_24h as (
    select
        d.coin_id,
        d.coin_name,
        d.symbol,
        d.close_price,
        d.daily_change_pct  as change_pct,
        d.avg_volume,
        '24h'               as period

    from {{ ref('gold_coin_daily') }} d
    cross join latest_date l

    where d.price_date = l.max_date
),

-- Данные за 7 дней
period_7d as (
    select
        d.coin_id,
        d.coin_name,
        d.symbol,

        -- Последняя цена в периоде
        max(case when d.price_date = l.max_date then d.close_price end) as close_price,

        round(
            (
                max(case when d.price_date = l.max_date then d.close_price end)
                - min(case when d.price_date >= l.max_date - interval '6 days' then d.close_price end)
            ) / nullif(
                min(case when d.price_date >= l.max_date - interval '6 days' then d.close_price end),
                0
            ) * 100,
            2
        ) as change_pct,

        avg(d.avg_volume) as avg_volume,
        '7d' as period

    from {{ ref('gold_coin_daily') }} d
    cross join latest_date l
    where d.price_date >= l.max_date - interval '6 days'
    group by d.coin_id, d.coin_name, d.symbol, l.max_date
),

-- Данные за 30 дней
period_30d as (
    select
        d.coin_id,
        d.coin_name,
        d.symbol,
        max(case when d.price_date = l.max_date then d.close_price end) as close_price,
        round(
            (
                max(case when d.price_date = l.max_date then d.close_price end)
                - min(case when d.price_date >= l.max_date - interval '29 days' then d.close_price end)
            ) / nullif(
                min(case when d.price_date >= l.max_date - interval '29 days' then d.close_price end),
                0
            ) * 100,
            2
        ) as change_pct,
        avg(d.avg_volume) as avg_volume,
        '30d' as period

    from {{ ref('gold_coin_daily') }} d
    cross join latest_date l
    where d.price_date >= l.max_date - interval '29 days'
    group by d.coin_id, d.coin_name, d.symbol, l.max_date
),

all_periods as (
    select * from period_24h
    union all
    select * from period_7d
    union all
    select * from period_30d
),

ranked as (
    select
        coin_id,
        coin_name,
        symbol,
        period,
        close_price,
        change_pct,
        avg_volume::bigint as avg_volume,

        -- Ранг среди растущих: 1 = наибольший рост
        rank() over (
            partition by period
            order by change_pct desc
        ) as gainer_rank,

        -- Ранг среди падающих: 1 = наибольшее падение
        rank() over (
            partition by period
            order by change_pct asc
        ) as loser_rank

    from all_periods
    where change_pct is not null
)

select
    coin_id,
    coin_name,
    symbol,
    period,
    close_price,
    change_pct,
    avg_volume,
    'gainer' as mover_type,
    gainer_rank as rank

from ranked
where gainer_rank <= 10

union all

select
    coin_id,
    coin_name,
    symbol,
    period,
    close_price,
    change_pct,
    avg_volume,
    'loser' as mover_type,
    loser_rank as rank

from ranked
where loser_rank <= 10

order by period, mover_type, rank
