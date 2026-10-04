select
    s.supplier_id,
    s.supplier_name,
    count(*) as shipments,
    avg(case when sh.actual_delivery_date <= po.expected_delivery_date then 1.0 else 0 end) as on_time_rate,
    avg(date_diff('day', po.expected_delivery_date, sh.actual_delivery_date)) as avg_delay_days
from {{ source('raw', 'shipments') }} sh
join {{ ref('stg_purchase_orders') }} po using (po_id)
join {{ source('raw', 'suppliers') }} s using (supplier_id)
group by 1, 2