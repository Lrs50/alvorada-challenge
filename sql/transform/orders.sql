with checked as (
    select
        r.*,
        case
            when nullif(trim(order_id), '') is null then 'blank order_id'
            when row_number() over (partition by trim(order_id) order by ctid) > 1
                then 'duplicate order_id'
            when nullif(trim(order_status), '') is null then 'blank order_status'
            when not exists (
                select 1 from core.customers c where c.customer_id = trim(r.customer_id)
            ) then 'unknown customer_id'
            when not coalesce(pg_input_is_valid(trim(order_purchase_timestamp), 'timestamp'), false)
                then 'invalid order_purchase_timestamp'
            when nullif(trim(order_delivered_customer_date), '') is not null
                and not pg_input_is_valid(trim(order_delivered_customer_date), 'timestamp')
                then 'invalid order_delivered_customer_date'
        end as reason
    from raw.orders r
),

loaded as (
    insert into core.orders (
        order_id, customer_id, order_status, order_purchase_timestamp, order_delivered_customer_date
    )
    select
        trim(order_id),
        trim(customer_id),
        trim(order_status),
        trim(order_purchase_timestamp)::timestamp,
        nullif(trim(order_delivered_customer_date), '')::timestamp
    from checked
    where reason is null
)

insert into ops.reject (run_id, source_table, row_data, reason)
select %s, 'orders', to_jsonb(c) - 'reason' - 'loaded_at', reason
from checked c
where reason is not null
