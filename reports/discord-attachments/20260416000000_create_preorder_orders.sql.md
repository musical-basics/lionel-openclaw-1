-- ============================================================================
-- Migration: create_preorder_orders
-- Creates the internal preorder order table for V1 imported Shopify snapshot.
--
-- Run in Supabase SQL Editor or via `supabase db push`.
-- See docs/preorder-order-layer-v1.md for full context.
-- ============================================================================

CREATE TABLE IF NOT EXISTS preorder_orders (

    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source traceability
    order_name          TEXT            NOT NULL,           -- Shopify order name, e.g. "#1103"
    raw_shopify_id      TEXT,                               -- Raw Shopify numeric ID from CSV
    import_batch_id     TEXT            NOT NULL,           -- Snapshot date slug, e.g. "2026-04-16"
    source              TEXT            NOT NULL DEFAULT 'shopify-csv',

    -- Customer
    email               TEXT            NOT NULL,           -- Normalized (lowercased)
    customer_name       TEXT,

    -- Order financials
    created_at          TIMESTAMPTZ     NOT NULL,           -- Shopify order created_at
    financial_status    TEXT,                               -- paid | authorized | partially_refunded
    fulfillment_status  TEXT,                               -- unfulfilled | fulfilled
    total_paid_usd      NUMERIC(10,2),                      -- Actual amount paid (from Shopify Total)

    -- Payment classification (V1 internal value)
    -- Derived from lineitem_name, NOT from the raw CSV payment_type column.
    -- full_payment | deposit_50 | waitlist_reservation
    payment_type        TEXT            NOT NULL,

    is_reservation      BOOLEAN         NOT NULL DEFAULT FALSE,

    -- Product metadata (parsed from lineitem_name at import time)
    lineitem_name       TEXT,                               -- Raw Shopify lineitem name
    product_line        TEXT,                               -- pro | bundle | keyboard_only | one | unknown
    size_variant        TEXT,                               -- DS5.5 | DS6.0 | NULL
    finish              TEXT,                               -- Black | White | Midnight Black | Aztec Gold | NULL

    -- Record timestamps
    inserted_at         TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),

    -- Idempotent import constraint
    CONSTRAINT preorder_orders_order_name_batch_key UNIQUE (order_name, import_batch_id)
);

-- Lookup indexes
CREATE INDEX IF NOT EXISTS preorder_orders_email_idx
    ON preorder_orders (email);

CREATE INDEX IF NOT EXISTS preorder_orders_import_batch_idx
    ON preorder_orders (import_batch_id);

CREATE INDEX IF NOT EXISTS preorder_orders_payment_type_idx
    ON preorder_orders (payment_type);

-- ── Row Level Security ────────────────────────────────────────────────────
-- Data is private: each authenticated user can only read rows matching their email.
-- All writes are done via the service role (import script / server actions only).

ALTER TABLE preorder_orders ENABLE ROW LEVEL SECURITY;

-- Authenticated buyers: read own records only
CREATE POLICY "buyers can read own preorder"
    ON preorder_orders
    FOR SELECT
    TO authenticated
    USING (email = lower(auth.email()));

-- Service role has unrestricted access (no RLS bypass needed — service role skips RLS by default)
