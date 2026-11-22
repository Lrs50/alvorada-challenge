with checked as (
    select
        r.*,
        case
            when not coalesce(pg_input_is_valid(trim(payment_sequential), 'integer'), false)
                then 'invalid payment_sequential'
            when not coalesce(pg_input_is_valid(trim(payment_installments), 'integer'), false)
                then 'invalid payment_installments'
            when not coalesce(pg_input_is_valid(trim(payment_value), 'numeric(12,2)'), false)
                then 'invalid payment_value'
            when nullif(trim(payment_type), '') is null then 'blank payment_type'
            when not exists (
                select 1 from core.orders o where o.order_id = trim(r.order_id)
            ) then 'unknown order_id'
            when row_number() over (
                partition by trim(order_id), trim(payment_sequential) order by ctid
            ) > 1 then 'duplicate order payment'
        end as reason
    from raw.order_payments r
),

loaded as (
    insert into core.order_payments (
        order_id, payment_sequential, payment_type, payment_installments, payment_value
    )
    select
        trim(order_id),
        trim(payment_sequential)::integer,
        trim(payment_type),
        trim(payment_installments)::integer,
        trim(payment_value)::numeric(12, 2)
    from checked
    where reason is null
)

insert into ops.reject (run_id, source_table, row_data, reason)
select %s, 'order_payments', to_jsonb(c) - 'reason' - 'loaded_at', reason
from checked c
where reason is not null
