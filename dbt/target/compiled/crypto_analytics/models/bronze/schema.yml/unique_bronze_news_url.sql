
    
    

select
    url as unique_field,
    count(*) as n_records

from "crypto_analytics"."bronze"."bronze_news"
where url is not null
group by url
having count(*) > 1


