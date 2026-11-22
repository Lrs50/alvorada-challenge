select
    date_trunc('month', o.order_purchase_timestamp)::date as month,
    c.customer_state,
    sum(i.price) as sales_value,
    count(distinct o.order_id) as orders,
    round(sum(i.price) / count(distinct o.order_id), 2) as avg_ticket
from core.orders o
join core.customers c using (customer_id)
join core.order_items i using (order_id)
where o.order_status = 'delivered'
group by month, c.customer_state
order by month, c.customer_state
