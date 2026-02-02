# Product Requirement Document

## AI-Powered Market Intelligence Dashboard — Skincare E-Commerce

| Field | Details |
|---|---|
| **Document Version** | 1.0 |
| **Status** | Draft |
| **Owner** | Senior Product Manager |
| **Last Updated** | 2026-02-01 |
| **Audience** | ML Engineers, Full-Stack Engineers, Data Scientists, Product Stakeholders |

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Goals and Non-Goals](#2-goals-and-non-goals)
3. [User Personas & User Stories](#3-user-personas--user-stories)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Data Model & Schema](#6-data-model--schema)
7. [System Architecture Overview](#7-system-architecture-overview)
8. [Dashboard Requirements](#8-dashboard-requirements)
9. [Evaluation & Monitoring Strategy](#9-evaluation--monitoring-strategy)
10. [Error Handling & Edge Cases](#10-error-handling--edge-cases)
11. [Security & Data Privacy](#11-security--data-privacy)
12. [Deployment & Environment Strategy](#12-deployment--environment-strategy)
13. [Rollout Plan](#13-rollout-plan-mvp--production)
14. [Future Enhancements Roadmap](#14-future-enhancements-roadmap)

---

## 1. Problem Statement

Indonesian e-commerce platforms generate massive volumes of skincare product data every day. However, this data arrives in a raw, unstructured form — product titles are noisy, inconsistently formatted, and often contain a mix of Indonesian and English text, abbreviations, promotional tags, and duplicate brand mentions. Fields such as brand name and product category are not explicitly provided; they must be inferred from the product title alone.

Without a reliable way to standardize and enrich this data, business stakeholders cannot perform meaningful analysis. Brand managers cannot accurately benchmark their portfolio against competitors. Market analysts lack a trustworthy signal to detect trends or shifts in consumer preference. Sellers are unable to make data-driven decisions about pricing, discounting, or inventory strategy.

The core problem is twofold:

**Data Quality.** Raw product titles cannot be directly used for aggregation or comparison. A single brand may appear as "Wardah," "wardah cosmetiques," "WARDAH SKINCARE," or "Wardah — Lightening Series." Without normalization, every variant becomes a separate data point, fragmenting any downstream analysis.

**Analytical Accessibility.** Even if the data were clean, the absence of an interactive, purpose-built dashboard means that insights remain buried in spreadsheets or raw query results. Stakeholders require a self-service analytical layer that exposes brand performance, pricing dynamics, rating correlations, and market positioning without requiring SQL proficiency.

This PRD defines an end-to-end AI-powered system that bridges the gap between raw e-commerce data and actionable market intelligence through a structured pipeline and a dedicated analytics dashboard.

---

## 2. Goals and Non-Goals

### 2.1 Goals

| ID | Goal | Success Criterion |
|---|---|---|
| G-01 | Ingest and persistently store raw skincare product data | 100% of ingested records are written to the raw data store without loss |
| G-02 | Extract and standardize brand names from unstructured titles | Brand extraction achieves ≥ 90% accuracy on a held-out validation set |
| G-03 | Classify products into a controlled taxonomy of product types | Classification achieves ≥ 85% accuracy; unknown-rate stays below 12% |
| G-04 | Assign calibrated confidence scores to all extracted fields | Confidence scores correlate with actual correctness (Brier score ≤ 0.15) |
| G-05 | Provide a real-time-capable API layer for dashboard consumption | P95 query latency ≤ 300 ms for standard dashboard filters |
| G-06 | Deliver an interactive dashboard for brand and product-type analysis | Stakeholder usability testing yields a task-completion rate ≥ 85% |
| G-07 | Support continuous model improvement via human-in-the-loop feedback | Feedback loop reduces error rate by ≥ 10% within two retraining cycles |

### 2.2 Non-Goals

- **Real-time price tracking or alerting.** The system analyzes historical and batch-ingested data; it does not crawl or monitor live listings.
- **Inventory or supply-chain management.** The dashboard is purely analytical; it does not trigger any purchasing or fulfillment actions.
- **Consumer-facing product recommendations.** The output is internal business intelligence, not a customer-facing product.
- **Multi-language translation or localization of the dashboard UI.** The dashboard will be delivered in English. Source data may contain Indonesian text, but the UI itself is not localized.
- **Image or video processing.** No product images or multimedia assets are in scope.
- **Direct integration with any specific e-commerce platform API.** Data ingestion is defined as a batch file or structured payload; live marketplace API integration is out of scope for v1.

---

## 3. User Personas & User Stories

### 3.1 Personas

#### Persona A — Brand Manager (Maya)
Maya oversees the digital presence of a mid-sized Indonesian skincare brand. She needs to understand how her brand's products perform relative to competitors in terms of sales volume, average rating, and effective pricing. She is comfortable with dashboards but does not write code.

#### Persona B — Market Analyst (Rizal)
Rizal conducts quarterly competitive landscape reports. He needs to slice data by product type, compare discount strategies across brands, and identify which product categories are growing or shrinking. He values export capability and drill-down depth.

#### Persona C — Marketplace Seller (Dina)
Dina sells multiple skincare brands on Indonesian e-commerce platforms. She needs a quick overview of which of her products are underperforming and why — whether due to pricing, low ratings, or unfavorable discount positioning relative to the category average.

### 3.2 User Stories

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-01 | *As a Brand Manager, I want to see my brand's total sales volume and average rating at a glance, so I can quickly assess overall health.* | A brand-level summary card displays total units sold, average rating, and average effective price, filterable by brand. |
| US-02 | *As a Market Analyst, I want to compare the average discount percentage across product types, so I can understand category-level pricing strategies.* | A grouped bar chart shows average discount % by product type, with the ability to filter by date range or brand. |
| US-03 | *As a Marketplace Seller, I want to identify products with a rating below the category average, so I can prioritize improvement efforts.* | A filterable table flags products whose rating falls below their product-type median, with a visual indicator. |
| US-04 | *As a Market Analyst, I want to explore the correlation between price, discount, and sales volume, so I can inform pricing strategy.* | A scatter plot renders price vs. quantity sold, optionally colored by discount tier or product type. |
| US-05 | *As a Brand Manager, I want to filter the entire dashboard by a specific brand, so I can focus my analysis on a single portfolio.* | Selecting a brand in the global filter instantly updates all dashboard widgets. |
| US-06 | *As a Market Analyst, I want to see which products have low AI-confidence scores, so I can assess data reliability before drawing conclusions.* | A data-quality indicator or filter allows users to exclude or highlight low-confidence records. |
| US-07 | *As a Marketplace Seller, I want to flag a misclassified product for correction, so the system learns from my feedback.* | An inline "Report an issue" action on any product row submits a correction to the feedback queue. |

---

## 4. Functional Requirements

### 4.1 Data Ingestion

| ID | Requirement | Priority |
|---|---|---|
| FR-ING-01 | The system shall accept product data via a structured batch payload (JSON or CSV) containing: product title, quantity sold, original price, discount, and rating. | P0 |
| FR-ING-02 | Each ingested record shall be assigned a unique, system-generated `raw_id` and a `created_at` timestamp upon receipt. | P0 |
| FR-ING-03 | The ingestion endpoint shall validate that all required fields are present and that numeric fields (price, discount, quantity, rating) conform to expected types and ranges. | P0 |
| FR-ING-04 | Invalid records shall be quarantined in a dedicated error log with a rejection reason; valid records shall proceed to the enrichment pipeline. | P1 |
| FR-ING-05 | The system shall support idempotent ingestion — duplicate payloads (detected via a content hash) shall not create duplicate records. | P1 |

### 4.2 Data Cleaning & Enrichment (Hybrid AI Pipeline)

This section defines the core AI pipeline. A hybrid approach is chosen over a single-model solution for the following reasons:

**Why Hybrid Over Single-Model:**

A transformer-only model would require substantial labeled training data — which is scarce for niche Indonesian skincare brands — and would be brittle against unseen brand names or misspellings. Conversely, rule-based systems alone cannot handle the long tail of noisy, inconsistent titles. The hybrid pipeline combines the precision of curated dictionaries and deterministic rules (which are fast, interpretable, and highly accurate for known entities) with the generalization capability of transformer models (which handle novel or ambiguous cases). This layered architecture also enables incremental improvement: each layer can be retrained or updated independently without destabilizing the others.

#### 4.2.1 Text Normalization

| ID | Requirement | Priority |
|---|---|---|
| FR-ENR-01 | Strip all leading/trailing whitespace; collapse internal whitespace runs to a single space. | P0 |
| FR-ENR-02 | Remove common promotional tags and noise tokens (e.g., "SALE," "NEW," "BEST SELLER," "FREE ONGKIR," "DISKON"). Maintain a configurable blocklist. | P0 |
| FR-ENR-03 | Normalize Unicode characters; convert to a canonical NFC form. | P0 |
| FR-ENR-04 | Lowercase the title for matching purposes while preserving a display-friendly cleaned version. | P0 |

#### 4.2.2 Brand Extraction

| ID | Requirement | Priority |
|---|---|---|
| FR-ENR-05 | **Layer 1 — Dictionary Lookup.** Maintain a curated brand dictionary (brand canonical name → list of known aliases and variants). Perform exact match against the normalized title. If a match is found, assign the canonical brand name with a confidence score of 0.95+. | P0 |
| FR-ENR-06 | **Layer 2 — Fuzzy Matching.** If Layer 1 yields no match, apply token-level fuzzy string matching (e.g., using a Levenshtein or Jaro-Winkler distance metric) against the brand dictionary. Accept matches above a configurable similarity threshold (default: 0.82). Assign confidence proportional to the similarity score. | P0 |
| FR-ENR-07 | **Layer 3 — Transformer Fallback.** If Layer 2 also yields no match above threshold, invoke a transformer-based model (NER or embedding-similarity against a brand embedding index). Assign the model's output confidence score directly. | P1 |
| FR-ENR-08 | If no layer produces a match above the minimum confidence floor (default: 0.60), assign brand as `"unknown"` with confidence `0.0`. | P0 |

#### 4.2.3 Product Type Classification

| ID | Requirement | Priority |
|---|---|---|
| FR-ENR-09 | Define and maintain a controlled taxonomy of product types (e.g., Moisturizer, Serum, Cleanser, Toner, Sunscreen, Mask, Eye Cream, Lip Care, Exfoliant). The taxonomy shall be versioned. | P0 |
| FR-ENR-10 | **Layer 1 — Rule-Based Keyword Detection.** Map a set of keywords and keyword phrases to each taxonomy class. Perform keyword matching against the normalized title. If one or more keywords match, assign the highest-priority class. | P0 |
| FR-ENR-11 | **Layer 2 — Transformer Embedding Similarity.** If no keyword rule fires, embed the normalized title using a pre-trained multilingual sentence transformer and compute cosine similarity against a pre-computed centroid embedding for each taxonomy class. Assign the class with the highest similarity score above a configurable threshold (default: 0.70). | P1 |
| FR-ENR-12 | If no layer produces a classification above threshold, assign product type as `"unknown"` with confidence `0.0`. | P0 |

#### 4.2.4 Confidence Scoring & Feedback

| ID | Requirement | Priority |
|---|---|---|
| FR-ENR-13 | Each enriched record shall carry three confidence fields: `brand_confidence`, `product_type_confidence`, and an overall `enrichment_confidence` (weighted average, configurable weights). | P0 |
| FR-ENR-14 | The system shall expose a feedback endpoint that accepts a `record_id` and corrected `brand` and/or `product_type` values. Corrections shall be persisted in a `feedback` table and flagged for retraining. | P1 |
| FR-ENR-15 | Accepted feedback shall be incorporated into the brand dictionary and keyword rule set on a scheduled retraining cycle (default: weekly). | P2 |

### 4.3 Aggregation-Ready Outputs

| ID | Requirement | Priority |
|---|---|---|
| FR-AGG-01 | After enrichment, produce and persist pre-aggregated metrics in a dedicated `aggregated_metrics` table. Supported aggregations include: total units sold, average price, average effective price (price × (1 − discount)), average rating, and product count — grouped by brand, product type, or both. | P0 |
| FR-AGG-02 | All aggregations shall support time-window grouping (daily, weekly, monthly). | P1 |
| FR-AGG-03 | Pre-aggregated metrics shall be refreshed on each ingestion batch completion. | P0 |

### 4.4 Dashboard Queries & Filters

| ID | Requirement | Priority |
|---|---|---|
| FR-DASH-01 | The API shall support filtering enriched product data by: brand, product type, rating range, price range, discount range, and confidence threshold. | P0 |
| FR-DASH-02 | The API shall support sorting results by any numeric field in ascending or descending order. | P0 |
| FR-DASH-03 | The API shall support pagination with configurable page size (default: 50, max: 500). | P0 |
| FR-DASH-04 | The API shall expose a dedicated endpoint returning pre-aggregated metrics, optionally filtered by the same dimensions as FR-DASH-01. | P0 |

---

## 5. Non-Functional Requirements

### 5.1 Latency

| ID | Requirement | Target |
|---|---|---|
| NFR-LAT-01 | Dashboard API query latency (P95) for standard filtered reads against pre-aggregated data. | ≤ 300 ms |
| NFR-LAT-02 | Dashboard API query latency (P95) for full-table filtered scans (e.g., product list with filters). | ≤ 800 ms |
| NFR-LAT-03 | End-to-end enrichment latency per batch (ingestion → enriched record persisted). | ≤ 60 seconds for batches up to 10,000 records |
| NFR-LAT-04 | Feedback submission and acknowledgement. | ≤ 2 seconds |

The system operates on a **batch processing** model for enrichment. Near-real-time enrichment is not required for v1; however, the pipeline shall be designed so that batch frequency can be reduced (e.g., from hourly to per-minute) without architectural change.

### 5.2 Accuracy & Confidence Thresholds

| Metric | Target |
|---|---|
| Brand extraction accuracy (on held-out test set) | ≥ 90% |
| Product type classification accuracy | ≥ 85% |
| Unknown-class rate (brand + product type combined) | ≤ 12% |
| Confidence score calibration (Brier score) | ≤ 0.15 |
| Minimum confidence floor for non-"unknown" assignment | 0.60 (configurable) |

### 5.3 Scalability

| ID | Requirement |
|---|---|
| NFR-SCALE-01 | The enrichment pipeline shall handle up to 100,000 records per batch without degradation in per-record processing time. |
| NFR-SCALE-02 | The database schema and query patterns shall remain performant up to 10 million total enriched records without manual index tuning beyond initial setup. |
| NFR-SCALE-03 | The API layer shall be horizontally scalable; adding instances shall linearly increase throughput. |

### 5.4 Cost Considerations

| Area | Guidance |
|---|---|
| Transformer inference | Batch inference should be preferred over per-record invocation to amortize GPU/CPU overhead. Consider quantized models or distilled variants to reduce per-inference cost. |
| Database | Supabase's managed PostgreSQL is cost-effective at expected data volumes (< 10 M rows). Monitor storage and connection usage monthly. |
| Hosting | Koyeb (backend) and Vercel (frontend) offer serverless/container tiers suitable for variable load. Set resource limits to prevent runaway costs. |
| Embedding index | A static or periodically refreshed embedding index (stored in-database or as a flat file) avoids the cost of an external vector database at current scale. Revisit if record count exceeds 50 M. |

---

## 6. Data Model & Schema

All tables are designed for Supabase (PostgreSQL). UUIDs are used as primary keys to support distributed ingestion if needed in the future. Row-level security (RLS) policies are assumed to be applied at the Supabase level.

### 6.1 Table: `raw_products`

Stores every record exactly as ingested, before any enrichment.

```sql
CREATE TABLE raw_products (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    content_hash    TEXT        NOT NULL UNIQUE,          -- SHA-256 of the raw payload; enforces idempotency
    title_raw       TEXT        NOT NULL,
    quantity_sold   INTEGER     NOT NULL CHECK (quantity_sold >= 0),
    price_original  NUMERIC(12,2) NOT NULL CHECK (price_original >= 0),
    discount        NUMERIC(5,4)  NOT NULL CHECK (discount BETWEEN 0 AND 1),  -- stored as fraction (0.0–1.0)
    rating          NUMERIC(3,1)  CHECK (rating BETWEEN 0 AND 5),
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source          TEXT                                  -- optional: identifies the ingestion batch or source system
);

CREATE INDEX idx_raw_products_ingested_at ON raw_products (ingested_at);
```

### 6.2 Table: `enriched_products`

Stores the cleaned and AI-enriched version of each product. Linked 1:1 to `raw_products`.

```sql
CREATE TABLE enriched_products (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_product_id          UUID        NOT NULL UNIQUE REFERENCES raw_products(id),
    title_cleaned           TEXT        NOT NULL,
    brand                   TEXT        NOT NULL,           -- canonical brand name or "unknown"
    product_type            TEXT        NOT NULL,           -- taxonomy label or "unknown"
    price_effective         NUMERIC(12,2) NOT NULL,         -- price_original * (1 - discount)
    brand_confidence        NUMERIC(3,2) NOT NULL CHECK (brand_confidence BETWEEN 0 AND 1),
    product_type_confidence NUMERIC(3,2) NOT NULL CHECK (product_type_confidence BETWEEN 0 AND 1),
    enrichment_confidence   NUMERIC(3,2) NOT NULL CHECK (enrichment_confidence BETWEEN 0 AND 1),
    brand_extraction_layer  TEXT        NOT NULL,           -- "dictionary" | "fuzzy" | "transformer" | "unknown"
    product_type_layer      TEXT        NOT NULL,           -- "keyword" | "transformer" | "unknown"
    enriched_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    taxonomy_version        TEXT        NOT NULL            -- version of the product type taxonomy used
);

CREATE INDEX idx_enriched_brand ON enriched_products (brand);
CREATE INDEX idx_enriched_product_type ON enriched_products (product_type);
CREATE INDEX idx_enriched_confidence ON enriched_products (enrichment_confidence);
```

### 6.3 Table: `brand_dictionary`

Curated reference table for brand extraction Layer 1.

```sql
CREATE TABLE brand_dictionary (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_canonical TEXT        NOT NULL,
    aliases         TEXT[]      NOT NULL DEFAULT '{}',     -- array of known variants/aliases
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_brand_dict_canonical ON brand_dictionary (brand_canonical);
```

### 6.4 Table: `product_type_taxonomy`

Versioned taxonomy definition.

```sql
CREATE TABLE product_type_taxonomy (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    version         TEXT        NOT NULL,
    label           TEXT        NOT NULL,                  -- e.g., "Moisturizer"
    keywords        TEXT[]      NOT NULL DEFAULT '{}',     -- keyword list for rule-based matching
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_taxonomy_version_label ON product_type_taxonomy (version, label);
```

### 6.5 Table: `aggregated_metrics`

Pre-computed aggregation results for fast dashboard queries.

```sql
CREATE TABLE aggregated_metrics (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    dimension_type      TEXT        NOT NULL CHECK (dimension_type IN ('brand', 'product_type', 'brand_product_type')),
    dimension_brand     TEXT,                              -- NULL when dimension_type = 'product_type'
    dimension_product_type TEXT,                           -- NULL when dimension_type = 'brand'
    time_bucket         DATE        NOT NULL,              -- start of the time window
    time_granularity    TEXT        NOT NULL CHECK (time_granularity IN ('daily', 'weekly', 'monthly')),
    total_units_sold    BIGINT      NOT NULL DEFAULT 0,
    avg_price_original  NUMERIC(12,2),
    avg_price_effective NUMERIC(12,2),
    avg_rating          NUMERIC(3,2),
    avg_discount        NUMERIC(5,4),
    product_count       INTEGER     NOT NULL DEFAULT 0,
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agg_dimension ON aggregated_metrics (dimension_type, dimension_brand, dimension_product_type);
CREATE INDEX idx_agg_time ON aggregated_metrics (time_bucket, time_granularity);
```

### 6.6 Table: `feedback`

Stores human corrections for continuous model improvement.

```sql
CREATE TABLE feedback (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    enriched_product_id     UUID        NOT NULL REFERENCES enriched_products(id),
    corrected_brand         TEXT,                          -- NULL if no brand correction
    corrected_product_type  TEXT,                          -- NULL if no product_type correction
    submitted_by            TEXT,                          -- user identifier or role
    submitted_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status                  TEXT        NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'applied', 'rejected'))
);

CREATE INDEX idx_feedback_status ON feedback (status);
```

### 6.7 Entity-Relationship Summary

```
raw_products (1) ──────── (1) enriched_products
                                    │
                                    │ (N)
                                    ▼
                                 feedback

brand_dictionary  ──────► [used by enrichment pipeline at runtime]
product_type_taxonomy ──► [used by enrichment pipeline at runtime]

enriched_products ──────► [source for] aggregated_metrics
```

---

## 7. System Architecture Overview

The system is decomposed into four distinct layers, each with clear boundaries and independent deployment concerns.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DASHBOARD FRONTEND                           │
│   Next.js (Vercel)                                                  │
│   ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐    │
│   │  KPI Cards  │  │   Charts &   │  │   Product Table &      │    │
│   │             │  │   Scatter    │  │   Feedback UI          │    │
│   └──────┬──────┘  └──────┬───────┘  └───────────┬────────────┘    │
│          │                │                       │                 │
└──────────┼────────────────┼───────────────────────┼─────────────────┘
           │  GraphQL / REST queries                 │ POST /feedback
           ▼                ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          API LAYER                                  │
│   Golang (Koyeb)                                                    │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │  Route Handler → Auth Middleware → Query Builder →        │      │
│   │  Supabase Client (via PostgREST or direct pg connection)  │      │
│   └──────────────────────────────────────────────────────────┘      │
│                          │                                          │
└──────────────────────────┼──────────────────────────────────────────┘
                           │ read (aggregated_metrics, enriched_products)
                           │ write (feedback)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DATABASE (Supabase)                          │
│   PostgreSQL                                                        │
│   ┌────────────┐ ┌──────────────┐ ┌─────────────────┐ ┌──────────┐ │
│   │raw_products│ │enriched_     │ │aggregated_      │ │feedback  │ │
│   │            │ │products      │ │metrics          │ │          │ │
│   └─────┬──────┘ └──────┬───────┘ └────────┬────────┘ └──────────┘ │
│         │               │                  │                        │
└─────────┼───────────────┼──────────────────┼────────────────────────┘
          │ write raw     │ write enriched   │ write aggregated
          ▼               ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   AI ENRICHMENT PIPELINE                            │
│   Python (Koyeb)                                                    │
│   ┌─────────────┐   ┌───────────────────┐   ┌───────────────────┐  │
│   │  Ingestion  │──►│  Text             │──►│  Brand Extraction │  │
│   │  Worker     │   │  Normalization    │   │  (3-Layer)        │  │
│   └─────────────┘   └───────────────────┘   └────────┬──────────┘  │
│                                                       │             │
│   ┌─────────────┐   ┌───────────────────┐   ┌───────▼──────────┐   │
│   │  Aggregation│◄──│  Confidence       │◄──│  Product Type    │   │
│   │  Refresh    │   │  Scoring          │   │  Classification  │   │
│   └─────────────┘   └───────────────────┘   │  (2-Layer)       │   │
│                                              └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.1 Layer Responsibilities

**AI Enrichment Pipeline (Python, Koyeb).** This is the intelligence core. It is responsible for consuming records from `raw_products`, executing the multi-layer brand extraction and product type classification, computing confidence scores, persisting results to `enriched_products`, and triggering the aggregation refresh. It runs as a scheduled batch job (configurable interval) or can be invoked on-demand via an internal trigger.

**Database (Supabase / PostgreSQL).** Acts as the single source of truth for all data states: raw, enriched, aggregated, and feedback. Pre-aggregated metrics tables ensure that dashboard queries remain fast regardless of the underlying enriched data volume.

**API Layer (Golang, Koyeb).** A stateless, high-performance HTTP service that exposes read endpoints for the dashboard and a write endpoint for feedback submission. Golang is chosen here for its low latency, efficient concurrency handling, and small binary footprint — ideal for a query-serving layer under variable load. It communicates with Supabase via standard PostgreSQL drivers or PostgREST.

**Dashboard Frontend (Next.js, Vercel).** A server-rendered React application that fetches data from the API layer and renders interactive visualizations. Next.js enables fast initial page loads via SSR and supports incremental static regeneration for semi-static pages. Deployment on Vercel provides edge caching and zero-config CI/CD.

---

## 8. Dashboard Requirements

### 8.1 KPIs (Key Performance Indicators)

The following KPIs shall be displayed as summary cards at the top of the dashboard, updating in response to active filters.

| KPI | Definition | Display Format |
|---|---|---|
| Total Products | Count of distinct enriched products matching current filters | Integer |
| Total Units Sold | Sum of `quantity_sold` across filtered products | Integer (formatted with thousand separators) |
| Average Rating | Mean of `rating` across filtered products | Decimal (1 dp) + star indicator |
| Average Effective Price | Mean of `price_effective` across filtered products | Currency (IDR or normalized) |
| Average Discount | Mean of `discount` across filtered products | Percentage (1 dp) |
| Unknown-Class Rate | Percentage of filtered products where brand or product_type is "unknown" | Percentage (1 dp) + warning indicator if > 10% |

### 8.2 Global Filters

The following filters shall be rendered in a persistent filter bar and shall apply to all dashboard widgets simultaneously.

| Filter | Type | Values |
|---|---|---|
| Brand | Multi-select dropdown | All canonical brands in the dataset + "unknown" |
| Product Type | Multi-select dropdown | All taxonomy labels + "unknown" |
| Rating Range | Dual-handle range slider | 0.0 – 5.0 |
| Price Range (Effective) | Dual-handle range slider | Min – Max in dataset |
| Discount Range | Dual-handle range slider | 0% – 100% |
| Minimum Confidence | Single slider | 0.0 – 1.0 (default: 0.0) |
| Time Period | Date range picker | Custom range or preset (Last 7d, 30d, 90d) |

### 8.3 Visualizations (Conceptual)

#### 8.3.1 Brand Performance Overview
**Type:** Horizontal bar chart (sorted by total units sold, descending).
**X-axis:** Total units sold.
**Y-axis:** Brand name.
**Purpose:** Enables quick comparison of brand-level sales volume. Tooltip shows avg. rating and avg. effective price.

#### 8.3.2 Product Type Distribution
**Type:** Pie or donut chart.
**Segments:** Product type labels.
**Metric:** Count of products or total units sold (toggle).
**Purpose:** Shows the composition of the market or a brand's portfolio by category.

#### 8.3.3 Price vs. Sales Volume Scatter Plot
**Type:** Scatter plot.
**X-axis:** Effective price.
**Y-axis:** Quantity sold.
**Color encoding:** Discount tier (e.g., Low: 0–10%, Medium: 11–30%, High: 31%+) or product type (selectable).
**Purpose:** Reveals pricing sweet spots and the relationship between price positioning and sales performance.

#### 8.3.4 Rating Distribution by Brand
**Type:** Box plot or grouped bar chart.
**X-axis:** Brand.
**Y-axis:** Rating.
**Purpose:** Allows comparison of rating consistency and median performance across brands.

#### 8.3.5 Trend Over Time
**Type:** Line chart.
**X-axis:** Time (daily/weekly/monthly, selectable).
**Y-axis:** Selectable metric (total units sold, avg. rating, avg. effective price, avg. discount).
**Color/series:** Optionally grouped by brand or product type.
**Purpose:** Supports trend analysis and identification of seasonal or promotional patterns.

#### 8.3.6 Product Detail Table
**Type:** Sortable, filterable data table.
**Columns:** Cleaned title, brand, product type, quantity sold, original price, effective price, discount, rating, brand confidence, product type confidence, extraction layers used.
**Actions:** "Report an issue" button per row (triggers feedback submission).
**Purpose:** Provides granular, drill-down access to individual product records.

---

## 9. Evaluation & Monitoring Strategy

### 9.1 Offline Evaluation

Before any model or pipeline update is promoted to production, it must pass offline evaluation on a held-out test set.

| Metric | Target | Evaluation Method |
|---|---|---|
| Brand extraction accuracy | ≥ 90% | Precision, recall, and F1 measured against a manually labeled sample of ≥ 500 records, stratified by extraction layer. |
| Product type classification accuracy | ≥ 85% | Precision, recall, and F1 per taxonomy class; macro-averaged. Confusion matrix reviewed for systematic misclassification patterns. |
| Unknown-class rate | ≤ 12% | Measured on a representative sample of at least 2,000 records drawn from the production data distribution. |
| Confidence calibration | Brier score ≤ 0.15 | Confidence scores binned into deciles; predicted vs. actual correctness plotted as a calibration curve. |

A regression test suite shall be maintained: a fixed set of annotated titles that must be correctly classified on every pipeline update. Any regression beyond a 2% delta triggers a block on promotion.

### 9.2 Dashboard Data Quality Checks

The dashboard shall surface data quality signals to users, enabling informed interpretation of results.

| Check | Implementation |
|---|---|
| Low-confidence record count | A badge or alert on the dashboard indicates how many records in the current view have `enrichment_confidence` below the active threshold. |
| Unknown-class proportion | The KPI bar displays the unknown-class rate; a warning indicator appears if it exceeds 10%. |
| Stale data indicator | The dashboard displays the timestamp of the most recent enrichment batch. If the batch is older than a configurable staleness threshold (default: 24 hours), a warning is shown. |
| Feedback backlog | An internal admin view (or a simple metric) tracks the number of pending feedback items awaiting review. |

---

## 10. Error Handling & Edge Cases

| Scenario | Handling Strategy |
|---|---|
| Missing or null required fields in ingestion payload | Record is rejected at validation; written to the error log with the specific field and reason. A count of rejections is reported in the batch summary. |
| Numeric fields out of expected range (e.g., rating > 5, negative price) | Treated as a validation error. Record is quarantined. |
| Product title is empty or contains only noise tokens after normalization | Brand and product type are both assigned `"unknown"` with confidence `0.0`. The record is still persisted in `enriched_products` for transparency. |
| Transformer model inference failure (timeout or OOM) | The pipeline catches the exception, skips the transformer layer for that record, and falls back to the previous layer's result or assigns `"unknown"`. An alert is logged. |
| Brand dictionary or taxonomy lookup returns multiple matches | For brand: the match with the highest fuzzy score is selected. For product type: the keyword rule with the highest defined priority wins. |
| Duplicate ingestion detected (matching `content_hash`) | The duplicate payload is silently acknowledged (HTTP 200) but no new record is created. A log entry is written. |
| Database write failure during enrichment | The pipeline implements exponential backoff with a maximum of 3 retries. If all retries fail, the record is flagged as `enrichment_failed` and included in the next batch. |
| Feedback submitted for a record that has since been re-enriched | The feedback is still persisted and linked to the original `enriched_product_id`. It is reviewed manually for applicability. |
| Very large batch (> 100,000 records) | The ingestion worker splits the batch into chunks of 10,000 records and processes them sequentially. Progress is tracked in a job-status table. |

---

## 11. Security & Data Privacy

| Area | Requirement |
|---|---|
| **Authentication & Authorization** | The API layer requires a valid API key or bearer token for all endpoints. Dashboard users authenticate via Supabase Auth (email/password or OAuth). Role-based access control (RBAC) is implemented: read-only for analysts, read+feedback for sellers, full admin for data ops. |
| **Data in Transit** | All communication between layers (frontend ↔ API, API ↔ database, pipeline ↔ database) is encrypted via TLS 1.2+. |
| **Data at Rest** | Supabase encrypts data at rest by default. No additional encryption layer is required at the application level for this data classification. |
| **Row-Level Security (RLS)** | Supabase RLS policies enforce that users can only access data permitted by their role. This is enforced at the database level, not solely in application code. |
| **PII Considerations** | The current dataset (product titles, prices, ratings) does not contain personally identifiable information. If seller-level data is introduced in future iterations, a PII audit and appropriate data-handling policy must be completed before ingestion. |
| **Vendor Lock-in Mitigation** | The system abstracts database access behind a repository/service layer. Supabase-specific features (e.g., RLS, Auth) are used but the core data model is standard PostgreSQL. Migration to another managed PostgreSQL provider requires only connection-string changes and RLS policy recreation. |
| **Secret Management** | API keys, database credentials, and model artifacts are stored in environment variables injected at deploy time by the hosting platform (Koyeb, Vercel). No secrets are committed to version control. |

---

## 12. Deployment & Environment Strategy

### 12.1 Environments

| Environment | Purpose | Infrastructure |
|---|---|---|
| **Development** | Local development and unit testing | Developer machines; local PostgreSQL via Docker or Supabase CLI |
| **Staging** | Integration testing, QA, and pre-production validation | Koyeb (backend + pipeline), Vercel (frontend), Supabase project (staging) |
| **Production** | Live system serving end users | Koyeb (backend + pipeline), Vercel (frontend), Supabase project (production) |

### 12.2 Deployment Configuration

| Component | Platform | Deployment Method |
|---|---|---|
| AI Enrichment Pipeline | Koyeb | Containerized (Docker). Runs as a scheduled job or a long-running worker process. |
| API Layer (Golang) | Koyeb | Containerized (Docker). Deployed as a stateless service with auto-scaling rules. |
| Dashboard Frontend | Vercel | Git-based deployment (push to `main` triggers production deploy; push to feature branches triggers preview deploys). |
| Database | Supabase | Managed service. Schema migrations are versioned and applied via a migration tool (e.g., Flyway or Supabase CLI migrations). |

### 12.3 CI/CD Pipeline

A single CI/CD pipeline (e.g., GitHub Actions) orchestrates the following on every merge to the relevant branch:

1. Lint and unit tests for all components.
2. Build Docker images for the pipeline and API layer.
3. Run integration tests against the staging Supabase database.
4. Run offline evaluation suite for the enrichment pipeline (if model artifacts have changed).
5. Deploy to staging (automatic) or production (manual gate or approval required).

---

## 13. Rollout Plan (MVP → Production)

### Phase 1 — MVP (Weeks 1–4)

**Scope:** Core pipeline and basic dashboard.

| Deliverable | Details |
|---|---|
| Data ingestion endpoint | Accepts JSON batch; validates and persists to `raw_products`. |
| Text normalization | Implements FR-ENR-01 through FR-ENR-04. |
| Brand extraction (Layer 1 + 2) | Dictionary lookup and fuzzy matching. Transformer fallback deferred. |
| Product type classification (Layer 1) | Keyword-based rules only. Transformer fallback deferred. |
| Confidence scoring | Basic scoring based on extraction layer and match quality. |
| Supabase schema | All tables deployed; indexes in place. |
| API layer (basic) | Read endpoints for enriched products and aggregated metrics. Pagination and sorting. |
| Dashboard (basic) | KPI cards, brand performance bar chart, product detail table. Global filter bar with brand and product type filters. |
| Offline evaluation | Initial test set created; baseline accuracy measured. |

**Success Criteria:** End-to-end flow works from ingestion to dashboard display. Brand accuracy ≥ 80% (relaxed from 90% due to limited dictionary); product type accuracy ≥ 75%.

### Phase 2 — Enhanced Pipeline (Weeks 5–7)

**Scope:** Transformer fallback, confidence calibration, and feedback loop.

| Deliverable | Details |
|---|---|
| Brand extraction Layer 3 | Transformer-based NER or embedding-similarity fallback. |
| Product type classification Layer 2 | Transformer embedding similarity fallback. |
| Confidence calibration | Scores are calibrated against validation data. Unknown-rate target enforced. |
| Feedback endpoint and UI | Users can flag misclassified products; corrections are persisted. |
| Aggregation refresh | Pre-aggregated metrics are computed and refreshed per batch. |
| Dashboard — time filters | Date range picker and trend line chart enabled. |

**Success Criteria:** Brand accuracy ≥ 90%; product type accuracy ≥ 85%; unknown-rate ≤ 12%. Feedback submission works end-to-end.

### Phase 3 — Production Hardening (Weeks 8–10)

**Scope:** Resilience, monitoring, and full dashboard feature set.

| Deliverable | Details |
|---|---|
| Error handling | All edge cases from Section 10 are implemented and tested. |
| Retry and failure recovery | Exponential backoff, batch chunking, and failed-record re-queuing. |
| Monitoring and alerting | Pipeline health, API latency, and data quality dashboards (internal). Alerts on error rate spikes or stale data. |
| Full dashboard | All visualizations from Section 8.3 are live. Confidence filter and data quality indicators are active. |
| Security hardening | RLS policies reviewed; RBAC enforced; secret management verified. |
| Retraining cycle | First automated retraining cycle incorporating feedback data is executed and validated. |
| Production deployment | Full CI/CD pipeline validated; production traffic enabled. |

**Success Criteria:** All NFRs met in production load testing. Stakeholder usability testing completed with ≥ 85% task-completion rate.

---

## 14. Future Enhancements Roadmap

The following enhancements are out of scope for the initial release but are architecturally anticipated. The current design decisions (modular pipeline layers, versioned taxonomy, feedback table, abstracted database access) are intentionally made to support these future capabilities without requiring foundational rework.

| Priority | Enhancement | Rationale |
|---|---|---|
| High | **Live marketplace API integration.** Ingest data directly from Indonesian e-commerce platform APIs (e.g., Tokopedia, Shopee) instead of relying on batch file uploads. | Reduces manual data preparation; enables more frequent freshness. |
| High | **Automated retraining pipeline.** Schedule periodic retraining of transformer models using accumulated feedback data, with automated evaluation gating. | Sustains and improves accuracy over time with minimal manual intervention. |
| Medium | **Competitor alerting.** Notify brand managers when a competitor's product enters a new category or achieves a significant rating or sales milestone. | Proactive intelligence beyond self-service exploration. |
| Medium | **Export and reporting.** Allow users to export filtered dashboard data to CSV or generate scheduled PDF/email reports. | Supports offline analysis workflows and executive reporting. |
| Medium | **Expanded taxonomy.** Introduce sub-categories (e.g., "Moisturizer → Day Cream," "Moisturizer → Night Cream") and support hierarchical filtering. | Enables deeper product-level granularity as the dataset grows. |
| Low | **Embedding index migration.** Replace the in-database embedding similarity approach with a dedicated vector database (e.g., pgvector extension or an external store) if the record count exceeds 50 million. | Ensures embedding search remains performant at scale. |
| Low | **Multi-language dashboard.** Localize the dashboard UI into Indonesian (Bahasa) for local stakeholders. | Improves accessibility for the primary user base. |
| Low | **Sentiment or review analysis.** If product review text becomes available in future data sources, integrate NLP-based sentiment scoring as an additional enrichment dimension. | Adds a qualitative signal to complement quantitative metrics. |

---

*End of Document*

---

*This PRD is a living document. It should be reviewed and updated at the start of each development sprint to reflect current priorities, emerging constraints, and lessons learned from previous phases.*
