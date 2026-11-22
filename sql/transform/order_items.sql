with checked as (
    select
        r.*,
        case
            when not coalesce(pg_input_is_valid(trim(order_item_id), 'integer'), false)
                then 'invalid order_item_id'
            when not coalesce(pg_input_is_valid(trim(price), 'numeric(12,2)'), false)
                then 'invalid price'
            when not coalesce(pg_input_is_valid(trim(freight_value), 'numeric(12,2)'), false)
                then 'invalid freight_value'
            when not exists (
                select 1 from core.orders o where o.order_id = trim(r.order_id)
            ) then 'unknown order_id'
            when not exists (
                select 1 from core.products p where p.product_id = trim(r.product_id)
            ) then 'unknown product_id'
            when row_number() over (
                partition by trim(order_id), trim(order_item_id) order by ctid
            ) > 1 then 'duplicate order item'
        end as reason
    from raw.order_items r
),

loaded as (
    insert into core.order_items (order_id, order_item_id, product_id, price, freight_value)
    select
        trim(order_id),
        trim(order_item_id)::integer,
        trim(product_id),
        trim(price)::numeric(12, 2),
        trim(freight_value)::numeric(12, 2)
    from checked
    where reason is null
)

insert into ops.reject (run_id, source_table, row_data, reason)
select %s, 'order_items', to_jsonb(c) - 'reason' - 'loaded_at', reason
from checked c
where reason is not null
