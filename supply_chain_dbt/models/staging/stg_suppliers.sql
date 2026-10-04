-- One row per supplier.
-- raw.suppliers has no status, active flag, or deleted flag, so every
-- source row is kept.

with source as (

    select * from {{ source('raw', 'suppliers') }}

),

final as (

    select
        supplier_id,
        supplier_name,
        country,
        lead_time_days,
        reliability_score
    from source

)

select * from final
