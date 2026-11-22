with checked as (
    select
        r.*,
        case
            when nullif(trim(customer_id), '') is null then 'blank customer_id'
            when nullif(trim(customer_unique_id), '') is null then 'blank customer_unique_id'
            when nullif(trim(customer_state), '') is null then 'blank customer_state'
            when row_number() over (partition by trim(customer_id) order by ctid) > 1
                then 'duplicate customer_id'
        end as reason
    from raw.customers r
),

loaded as (
    insert into core.customers (customer_id, customer_unique_id, customer_state)
    select trim(customer_id), trim(customer_unique_id), trim(customer_state)
    from checked
    where reason is null
)

insert into ops.reject (run_id, source_table, row_data, reason)
select %s, 'customers', to_jsonb(c) - 'reason' - 'loaded_at', reason
from checked c
where reason is not null
