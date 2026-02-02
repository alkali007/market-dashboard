-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Raw Products Table
-- content_hash is the stable identifier (Name + URL)
CREATE TABLE IF NOT EXISTS raw_products (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_hash    TEXT        NOT NULL UNIQUE,
    title_raw       TEXT        NOT NULL,
    quantity_sold   BIGINT      NOT NULL DEFAULT 0,
    price_original  NUMERIC(12,2) NOT NULL DEFAULT 0,
    price_current   NUMERIC(12,2) NOT NULL DEFAULT 0,
    discount        NUMERIC(5,4)  NOT NULL DEFAULT 0,
    rating          NUMERIC(3,1)  DEFAULT 0,
    url             TEXT,
    image_url       TEXT,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Enriched Products Table
CREATE TABLE IF NOT EXISTS enriched_products (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    raw_product_id          UUID        NOT NULL UNIQUE REFERENCES raw_products(id) ON DELETE CASCADE,
    title_cleaned           TEXT        NOT NULL,
    brand                   TEXT        NOT NULL,
    product_type            TEXT        NOT NULL,
    price_effective         NUMERIC(12,2) NOT NULL,
    brand_confidence        NUMERIC(3,2) NOT NULL DEFAULT 0,
    product_type_confidence NUMERIC(3,2) NOT NULL DEFAULT 0,
    enrichment_confidence   NUMERIC(3,2) NOT NULL DEFAULT 0,
    enriched_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexing for performance
CREATE INDEX IF NOT EXISTS idx_enriched_brand ON enriched_products (brand);
CREATE INDEX IF NOT EXISTS idx_enriched_product_type ON enriched_products (product_type);

-- 3. Analytics Master View
-- This view flattens raw and enriched data for the Dashboard
CREATE OR REPLACE VIEW analytics_master AS
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
