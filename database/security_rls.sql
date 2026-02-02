-- Enable Row Level Security (RLS) on all tables
ALTER TABLE raw_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE enriched_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_master ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any (to avoid duplicates)
DROP POLICY IF EXISTS "Service role can do everything on raw_products" ON raw_products;
DROP POLICY IF EXISTS "Service role can do everything on enriched_products" ON enriched_products;
DROP POLICY IF EXISTS "Service role can do everything on analytics_master" ON analytics_master;

-- Create policies for service_role (the role used by your API connection string)
-- These policies allow the API full access while blocking internal/public users.

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

CREATE POLICY "Service role can do everything on analytics_master" 
ON analytics_master 
TO service_role 
USING (true) 
WITH CHECK (true);

-- Explicitly block any other access (anonymous or authenticated user roles)
-- By enabling RLS without 'USING (true)' policies for 'anon' or 'authenticated', 
-- Supabase blocks all access from those roles by default.
