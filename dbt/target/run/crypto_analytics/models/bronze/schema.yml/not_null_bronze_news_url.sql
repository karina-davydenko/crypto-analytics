
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select url
from "crypto_analytics"."bronze"."bronze_news"
where url is null



  
  
      
    ) dbt_internal_test