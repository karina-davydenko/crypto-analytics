
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    url as unique_field,
    count(*) as n_records

from "crypto_analytics"."bronze"."bronze_news"
where url is not null
group by url
having count(*) > 1



  
  
      
    ) dbt_internal_test