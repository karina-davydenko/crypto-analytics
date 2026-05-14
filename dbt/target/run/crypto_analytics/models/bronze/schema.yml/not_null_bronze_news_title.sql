
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select title
from "crypto_analytics"."bronze"."bronze_news"
where title is null



  
  
      
    ) dbt_internal_test