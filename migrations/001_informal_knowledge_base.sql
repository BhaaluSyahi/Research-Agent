-- Migration 001: Informal Knowledge Base
-- Run in Supabase SQL editor. Do NOT run in application code.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE informal_news_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_hash TEXT UNIQUE NOT NULL,      -- SHA256 of raw text. Primary dedup key.
    title TEXT,
    summary TEXT NOT NULL,                  -- GPT-4o generated summary (2-4 sentences)
    raw_snippet TEXT,                       -- Original text before summarization
    source_url TEXT NOT NULL,
    source_domain TEXT,                     -- Extracted domain, e.g. 'thehindu.com'
    trust_score FLOAT CHECK (trust_score >= 0 AND trust_score <= 1),
    entities JSONB,                         -- {"people": [], "orgs": [], "locations": [], "events": []}
    topic_tags TEXT[],                      -- e.g., ['floods', 'Kerala', 'rescue']
    geo_tags TEXT[],                        -- Normalized geography: ['kerala', 'india']
    event_date DATE,                        -- When the event happened (extracted or null)
    indexed_at TIMESTAMPTZ DEFAULT NOW(),
    last_validated_at TIMESTAMPTZ,          -- When trust score was last re-evaluated
    embedding VECTOR(768),                 -- text-embedding-3-small output
    is_active BOOLEAN DEFAULT TRUE,         -- FALSE = soft deleted
    version INTEGER DEFAULT 1,             -- Optimistic locking for concurrent updates
    indexed_by TEXT                         -- Which agent indexed this: 'floods_agent', 'on_demand', etc.
);

CREATE INDEX ON informal_news_entries USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON informal_news_entries USING GIN (topic_tags);
CREATE INDEX ON informal_news_entries USING GIN (geo_tags);
CREATE INDEX ON informal_news_entries (event_date);
CREATE INDEX ON informal_news_entries (is_active);

-- Many-to-many: entries ↔ topics
CREATE TABLE entry_topics (
    entry_id UUID NOT NULL REFERENCES informal_news_entries(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,                    -- matches search_strategy.topic
    relevance_score FLOAT,                  -- 0-1, how relevant is this entry to this topic
    added_by TEXT NOT NULL,                 -- agent name that created the association
    added_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (entry_id, topic)
);
