-- Enable Row Level Security (RLS) on all TIED tables
-- (RLS cannot be applied to Views directly)
ALTER TABLE raw_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE enriched_products ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "Service role can do everything on raw_products" ON raw_products;
DROP POLICY IF EXISTS "Service role can do everything on enriched_products" ON enriched_products;

-- Create policies for service_role
CREATE POLICY "Service role can do everything on raw_products" 
ON raw_products 
TO service_role 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Service role can do everything on enriched_products" 
ON enriched_products 
TO service_role 
USING (true) 
WITH CHECK (true);

-- To ensure the Analytics View respects these policies:
-- We recreate the view with security_invoker = true
-- This ensures that whoever queries the view must pass RLS checks on the tables below.
CREATE OR REPLACE VIEW analytics_master 
WITH (security_invoker = on)
AS
 SELECT e.id,
    e.brand,
    e.product_type,
    e.price_effective,
    r.title_raw,
    r.quantity_sold,
    r.rating,
    r.discount,
    r.price_original,
    r.price_current,
    (r.quantity_sold::numeric * e.price_effective) AS revenue_proxy,
        CASE
            WHEN r.discount <= 0.1 THEN 'Low'::text
            WHEN r.discount <= 0.3 THEN 'Medium'::text
            ELSE 'High'::text
        END AS discount_tier
   FROM enriched_products e
     JOIN raw_products r ON e.raw_product_id = r.id;
