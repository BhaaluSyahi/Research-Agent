-- Migration 003: KPIs and Logs
-- Run in Supabase SQL editor. Do NOT run in application code.

CREATE TABLE matching_kpis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id UUID NOT NULL,               -- references requests.id (no FK — core backend table)
    pipeline_started_at TIMESTAMPTZ NOT NULL,
    pipeline_completed_at TIMESTAMPTZ,
    formal_matches_count INTEGER DEFAULT 0,
    informal_matches_count INTEGER DEFAULT 0,
    on_demand_triggered BOOLEAN DEFAULT FALSE,
    on_demand_articles_added INTEGER DEFAULT 0,
    rag_top_score FLOAT,                    -- cosine score of best RAG match
    rag_results_count INTEGER DEFAULT 0,
    sufficiency_met BOOLEAN,                -- was RAG sufficient without on-demand?
    total_latency_ms INTEGER,
    topics_classified TEXT[],               -- what topics the request was classified into
    geo_extracted TEXT[],                   -- what geographies were extracted from request
    error_occurred BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON matching_kpis (request_id);
CREATE INDEX ON matching_kpis (created_at);
CREATE INDEX ON matching_kpis (on_demand_triggered);

CREATE TABLE crawl_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name TEXT NOT NULL,               -- e.g., 'floods_agent'
    run_type TEXT NOT NULL,                 -- 'scheduled' | 'on_demand'
    topic TEXT NOT NULL,
    search_query TEXT,
    tavily_results_count INTEGER,
    new_entries_count INTEGER,
    skipped_count INTEGER,
    failed_count INTEGER,
    duration_ms INTEGER,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
