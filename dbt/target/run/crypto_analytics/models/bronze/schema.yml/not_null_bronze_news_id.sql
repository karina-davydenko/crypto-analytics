
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select id
from "crypto_analytics"."bronze"."bronze_news"
where id is null



  
  
      
    ) dbt_internal_test