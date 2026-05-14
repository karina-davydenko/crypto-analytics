
    
    

select
    id as unique_field,
    count(*) as n_records

from "crypto_analytics"."bronze"."bronze_prices"
where id is not null
group by id
having count(*) > 1


