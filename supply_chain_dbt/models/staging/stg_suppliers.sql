select
    supplier_id,
    supplier_name,
    country,
    lead_time_days,
    reliability_score
from {{ source('raw', 'suppliers') }}
