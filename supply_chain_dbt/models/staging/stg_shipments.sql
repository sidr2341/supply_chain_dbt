select
    shipment_id,
    po_id,
    carrier,
    cast(ship_date as date) as ship_date,
    cast(actual_delivery_date as date) as actual_delivery_date
from {{ source('raw', 'shipments') }}
