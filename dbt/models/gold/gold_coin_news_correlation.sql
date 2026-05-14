-- gold_coin_news_correlation: цена + новости + sentiment по монете и дате.
--
-- Связывает ценовые данные с новостями через coin_mentions.
-- Позволяет увидеть: влияют ли новости на цену монеты?
-- LAG функция сдвигает цену на -1 день чтобы проверить корреляцию.

with news_daily as (
    select
        n.coin_mention                              as coin_id,
        date_trunc('day', sn.published_at)::date   as news_date,
        count(*)                                    as news_count,
        round(avg(sn.sentiment_score)::numeric, 4)  as avg_sentiment,

        -- Считаем сколько позитивных, негативных и нейтральных новостей за день
        count(*) filter (where sn.sentiment_label = 'positive') as positive_count,
        count(*) filter (where sn.sentiment_label = 'negative') as negative_count,
        count(*) filter (where sn.sentiment_label = 'neutral')  as neutral_count

    from {{ ref('silver_news') }} sn
    cross join lateral unnest(sn.coin_mentions) as n(coin_mention)
    where sn.published_at is not null
    group by n.coin_mention, date_trunc('day', sn.published_at)::date
),

prices_daily as (
    select
        coin_id,
        coin_name,
        symbol,
        price_date,
        close_price,
        daily_change_pct,
        ma_7d,
        avg_volume

    from {{ ref('gold_coin_daily') }}
),

joined as (
    select
        p.coin_id,
        p.coin_name,
        p.symbol,
        p.price_date,
        p.close_price,
        p.daily_change_pct,
        p.ma_7d,
        p.avg_volume,

        -- Если новостей нет — подставляем 0 через COALESCE
        coalesce(n.news_count,     0)        as news_count,
        coalesce(n.avg_sentiment,  0.0)      as avg_sentiment,
        coalesce(n.positive_count, 0)        as positive_count,
        coalesce(n.negative_count, 0)        as negative_count,
        coalesce(n.neutral_count,  0)        as neutral_count

    from prices_daily p
    left join news_daily n
        on p.coin_id   = n.coin_id
        and p.price_date = n.news_date
),

final as (
    select
        coin_id,
        coin_name,
        symbol,
        price_date,
        close_price,
        daily_change_pct,
        ma_7d,
        avg_volume,
        news_count,
        avg_sentiment,
        positive_count,
        negative_count,
        neutral_count,

        lag(news_count, 1) over (
            partition by coin_id
            order by price_date asc
        ) as news_count_prev_day,

        lag(avg_sentiment, 1) over (
            partition by coin_id
            order by price_date asc
        ) as avg_sentiment_prev_day

    from joined
)

select * from final
order by coin_id, price_date
