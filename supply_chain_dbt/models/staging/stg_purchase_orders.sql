-- One row per active purchase order.
-- status identifies the record: Open and Received are active. Cancelled
-- orders are inactive and excluded. Order dates are cast to dates.

with source as (

    select * from {{ source('raw', 'purchase_orders') }}

),

final as (

    select
        po_id,
        supplier_id,
        warehouse_id,
        cast(order_date as date) as order_date,
        cast(expected_delivery_date as date) as expected_delivery_date,
        status
    from source
    where status in ('Open', 'Received')

)

select * from final
