
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select fetched_at
from "crypto_analytics"."bronze"."bronze_prices"
where fetched_at is null



  
  
      
    ) dbt_internal_test