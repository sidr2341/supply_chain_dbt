-- One row per supplier.
-- Joins each inbound shipment to its purchase order on po_id, then to the
-- supplier on supplier_id. A shipment with no matching order, or an order
-- with no matching supplier, is dropped.
-- on_time_rate is the share of shipments delivered on or before the expected
-- date. avg_delay_days is the average of actual minus expected, in days
-- (negative means early).

with shipments as (

    select
        shipment_id,
        po_id,
        actual_delivery_date
    from {{ ref('stg_shipments') }}

),

purchase_orders as (

    select
        po_id,
        supplier_id,
        expected_delivery_date
    from {{ ref('stg_purchase_orders') }}

),

suppliers as (

    select
        supplier_id,
        supplier_name
    from {{ ref('stg_suppliers') }}

),

shipment_deliveries as (

    select
        suppliers.supplier_id,
        suppliers.supplier_name,
        shipments.shipment_id,
        shipments.actual_delivery_date,
        purchase_orders.expected_delivery_date
    from shipments
    inner join purchase_orders
        on shipments.po_id = purchase_orders.po_id
    inner join suppliers
        on purchase_orders.supplier_id = suppliers.supplier_id

)

select
    supplier_id,
    supplier_name,
    count(*) as shipments,
    avg(
        case
            when actual_delivery_date <= expected_delivery_date then 1.0
            else 0
        end
    ) as on_time_rate,
    avg(date_diff('day', expected_delivery_date, actual_delivery_date)) as avg_delay_days
from shipment_deliveries
group by supplier_id, supplier_name
