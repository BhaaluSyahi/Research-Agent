-- Migration 002: Search Strategy
-- Run in Supabase SQL editor. Do NOT run in application code.

CREATE TABLE search_strategy (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic TEXT UNIQUE NOT NULL,             -- matches queue name suffix: 'floods', 'drought', etc.
    display_name TEXT,                      -- Human-readable: 'Flood Relief'
    search_queries JSONB NOT NULL,          -- [{"query": "NGO flood relief India 2025", "weight": 1.0}, ...]
    geo_focus TEXT[],                       -- ['kerala', 'assam'] or empty for national
    crawl_frequency_hours INTEGER DEFAULT 6,
    priority INTEGER DEFAULT 5,             -- 1 (highest) to 10 (lowest)
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMPTZ,
    last_run_articles_found INTEGER,
    last_run_new_entries INTEGER,
    updated_by TEXT DEFAULT 'system',       -- 'system' or 'strategy_module'
    notes TEXT,                             -- Free text rationale for current strategy
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
