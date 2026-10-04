-- One row per inbound shipment.
-- raw.shipments has no status, active flag, or deleted flag, so every
-- source row is kept. Ship and delivery timestamps are cast to dates.

with source as (

    select * from {{ source('raw', 'shipments') }}

),

final as (

    select
        shipment_id,
        po_id,
        carrier,
        cast(ship_date as date) as ship_date,
        cast(actual_delivery_date as date) as actual_delivery_date
    from source

)

select * from final
