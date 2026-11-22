with category_sales as (
    select
        date_trunc('month', o.order_purchase_timestamp)::date as month,
        coalesce(p.product_category_name, 'unknown') as product_category,
        sum(i.price) as sales_value
    from core.orders o
    join core.order_items i using (order_id)
    join core.products p using (product_id)
    where o.order_status = 'delivered'
    group by month, product_category
),

ranked as (
    select
        month,
        product_category,
        sales_value,
        row_number() over (
            partition by month
            order by sales_value desc, product_category
        ) as rank
    from category_sales
)

select month, rank, product_category, sales_value
from ranked
where rank <= 10
order by month, rank
