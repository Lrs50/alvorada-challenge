with checked as (
    select
        r.*,
        case
            when nullif(trim(product_id), '') is null then 'blank product_id'
            when row_number() over (partition by trim(product_id) order by ctid) > 1
                then 'duplicate product_id'
        end as reason
    from raw.products r
),

loaded as (
    insert into core.products (product_id, product_category_name)
    select trim(product_id), nullif(trim(product_category_name), '')
    from checked
    where reason is null
)

insert into ops.reject (run_id, source_table, row_data, reason)
select %s, 'products', to_jsonb(c) - 'reason' - 'loaded_at', reason
from checked c
where reason is not null
