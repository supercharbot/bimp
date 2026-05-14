-- Migration: Add triage support
-- Run: sudo -u postgres psql -d bimp -f store/migrations/add_triage.sql

-- Triage rules table — tenant-scoped filter rules built during onboarding
CREATE TABLE IF NOT EXISTS triage_rules (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    rule_type TEXT NOT NULL,      -- 'block_sender', 'block_pattern', 'allow_sender'
    value TEXT NOT NULL,           -- domain, email address, or pattern
    target TEXT NOT NULL DEFAULT 'sender',  -- 'sender' or 'subject'
    source TEXT NOT NULL DEFAULT 'auto',    -- 'auto' (onboarding/pipeline) or 'manual' (command centre)
    created_at TIMESTAMP DEFAULT NOW()
);

-- Prevent duplicate rules per tenant
CREATE UNIQUE INDEX IF NOT EXISTS uq_triage_rule
    ON triage_rules (tenant_id, rule_type, value, target);

-- Fast lookup by tenant
CREATE INDEX IF NOT EXISTS idx_triage_rules_tenant
    ON triage_rules (tenant_id);

-- Track triage outcome on documents
ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS triage_status TEXT DEFAULT NULL;
    -- Values: 'passed', 'skipped', NULL (pre-triage documents)
