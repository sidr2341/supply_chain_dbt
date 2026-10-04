select
    po_id,
    supplier_id,
    warehouse_id,
    cast(order_date as date) as order_date,
    cast(expected_delivery_date as date) as expected_delivery_date,
    status
from {{ source('raw', 'purchase_orders') }}