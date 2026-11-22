with item_totals as (
    select order_id, sum(price + freight_value) as items_total
    from core.order_items
    group by order_id
),

payment_totals as (
    select order_id, sum(payment_value) as paid_total
    from core.order_payments
    group by order_id
),

compared as (
    select
        o.order_id,
        o.order_status,
        i.items_total,
        p.paid_total,
        coalesce(p.paid_total, 0) - coalesce(i.items_total, 0) as difference
    from core.orders o
    left join item_totals i using (order_id)
    left join payment_totals p using (order_id)
)

select
    order_id,
    order_status,
    coalesce(items_total, 0) as items_total,
    coalesce(paid_total, 0) as paid_total,
    difference,
    case
        when paid_total is null then 'no payment'
        when items_total is null then 'no items'
        when difference > 0 then 'paid more'
        else 'paid less'
    end as reason
from compared
where paid_total is null or abs(difference) > 0.01
order by abs(difference) desc, order_id
