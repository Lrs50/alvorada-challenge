with order_sales as (
    select
        order_id,
        sum(price) as sales_value
    from core.order_items
    group by order_id
)
select
    date_trunc('month', o.order_purchase_timestamp)::date as month,
    c.customer_state,
    sum(s.sales_value) as sales_value,
    count(*) as orders,
    round(sum(s.sales_value) / count(*), 2) as avg_ticket
from core.orders o
join core.customers c using (customer_id)
join order_sales s using (order_id)
where o.order_status = 'delivered'
group by month, c.customer_state
order by month, c.customer_state
