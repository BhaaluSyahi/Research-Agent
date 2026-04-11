-- Migration 004: RPC for pgvector similarity search
-- Run in Supabase SQL editor.

CREATE OR REPLACE FUNCTION match_informal_entries (
  query_embedding vector(1536),
  match_count int,
  min_trust float,
  filter_topic_tags text[] DEFAULT null,
  filter_geo_tags text[] DEFAULT null
) RETURNS TABLE (
  id uuid,
  content_hash text,
  title text,
  summary text,
  raw_snippet text,
  source_url text,
  source_domain text,
  trust_score float,
  entities jsonb,
  topic_tags text[],
  geo_tags text[],
  event_date date,
  indexed_at timestamptz,
  last_validated_at timestamptz,
  is_active boolean,
  version int,
  indexed_by text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    e.id,
    e.content_hash,
    e.title,
    e.summary,
    e.raw_snippet,
    e.source_url,
    e.source_domain,
    e.trust_score,
    e.entities,
    e.topic_tags,
    e.geo_tags,
    e.event_date,
    e.indexed_at,
    e.last_validated_at,
    e.is_active,
    e.version,
    e.indexed_by,
    1 - (e.embedding <=> query_embedding) AS similarity
  FROM informal_news_entries e
  WHERE e.is_active = true
    AND e.trust_score >= min_trust
    AND (filter_topic_tags IS NULL OR e.topic_tags && filter_topic_tags)
    AND (filter_geo_tags IS NULL OR e.geo_tags && filter_geo_tags)
  ORDER BY e.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
