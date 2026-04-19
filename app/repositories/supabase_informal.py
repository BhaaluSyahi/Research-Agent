"""
SupabaseInformalRepository — CRUD for the informal knowledge base tables.
Owns: informal_news_entries, entry_topics.
"""

import asyncio
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from supabase import AsyncClient

from app.core.exceptions import OptimisticLockError, RepositoryError
from app.core.logging import get_logger
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


# ── Domain Models ─────────────────────────────────────────────────────────────

class InformalEntryEntities(BaseModel):
    """Extracted entities from an article."""
    people: list[str] = []
    orgs: list[str] = []
    locations: list[str] = []
    events: list[str] = []


class InformalEntry(BaseModel):
    """Full record from informal_news_entries."""
    id: UUID
    content_hash: str
    title: Optional[str] = None
    summary: str
    raw_snippet: Optional[str] = None
    source_url: str
    source_domain: Optional[str] = None
    trust_score: Optional[float] = None
    entities: Optional[InformalEntryEntities] = None
    topic_tags: list[str] = []
    geo_tags: list[str] = []
    event_date: Optional[date] = None
    indexed_at: datetime
    last_validated_at: Optional[datetime] = None
    is_active: bool = True
    version: int = 1
    indexed_by: Optional[str] = None
    similarity: float = 0.0                 # Cosine similarity score returned by RPC
    # NOTE: embedding is excluded — it's a VECTOR type not returned by default selects


class InformalEntryCreate(BaseModel):
    """Input model for creating/upserting an informal_news_entries row."""
    content_hash: str
    title: Optional[str] = None
    summary: str
    raw_snippet: Optional[str] = None
    source_url: str
    source_domain: Optional[str] = None
    trust_score: Optional[float] = None
    entities: Optional[InformalEntryEntities] = None
    topic_tags: list[str] = []
    geo_tags: list[str] = []
    event_date: Optional[date] = None
    embedding: list[float]                  # 768-dimensional (Gemini)
    indexed_by: str
    version: int = 1                        # used for optimistic lock on create


class SearchFilters(BaseModel):
    """Filters applied to the pgvector similarity search."""
    topic_tags: list[str] = []
    geo_tags: list[str] = []
    min_trust_score: float = 0.3            # floored by guardrail before reaching here
    top_k: int = 20                         # capped at 20 by guardrail


# ── Repository ────────────────────────────────────────────────────────────────

class SupabaseInformalRepository(BaseRepository):
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def get_by_content_hash(self, content_hash: str) -> InformalEntry | None:
        """Return an entry matching the SHA256 content hash, or None."""
        try:
            response = await (
                self.client.table("informal_news_entries")
                .select(
                    "id, content_hash, title, summary, raw_snippet, source_url, "
                    "source_domain, trust_score, entities, topic_tags, geo_tags, "
                    "event_date, indexed_at, last_validated_at, is_active, version, indexed_by"
                )
                .eq("content_hash", content_hash)
                .limit(1)
                .execute()
            )
            if not response.data:
                return None
            return InformalEntry.model_validate(response.data[0])
        except Exception as exc:
            logger.error(
                "get_by_content_hash_failed",
                module="repositories",
                operation="get_by_content_hash",
                error=str(exc),
            )
            raise RepositoryError(f"Failed to fetch entry by content_hash: {exc}") from exc

    async def upsert_entry(self, entry: InformalEntryCreate) -> InformalEntry:
        """
        Insert or update an informal knowledge entry.
        Uses optimistic locking (version field) before update.
        content_hash is the dedup key.
        """
        try:
            # Check if an existing row exists
            existing = await self.get_by_content_hash(entry.content_hash)

            if existing is not None:
                # Optimistic lock: only update if version matches
                if existing.version != entry.version:
                    raise OptimisticLockError(
                        f"Version mismatch for content_hash={entry.content_hash}: "
                        f"expected {entry.version}, found {existing.version}"
                    )
                # Update trust score if the new entry has a higher one
                new_version = existing.version + 1
                payload = entry.model_dump(mode="json", exclude={"version"})
                payload["version"] = new_version
                payload["is_active"] = True

                response = await (
                    self.client.table("informal_news_entries")
                    .update(payload)
                    .eq("content_hash", entry.content_hash)
                    .execute()
                )
                row = response.data[0] if response.data else None
            else:
                # New entry — insert
                payload = entry.model_dump(mode="json")
                payload["is_active"] = True
                response = await (
                    self.client.table("informal_news_entries")
                    .insert(payload)
                    .execute()
                )
                row = response.data[0] if response.data else None

            if not row:
                raise RepositoryError("Upsert returned no data")

            logger.info(
                "informal_entry_upserted",
                module="repositories",
                operation="upsert_entry",
                content_hash=entry.content_hash,
                indexed_by=entry.indexed_by,
            )
            return InformalEntry.model_validate(row)

        except (OptimisticLockError, RepositoryError):
            raise
        except Exception as exc:
            logger.error(
                "upsert_entry_failed",
                module="repositories",
                operation="upsert_entry",
                content_hash=entry.content_hash,
                error=str(exc),
            )
            raise RepositoryError(f"Failed to upsert informal entry: {exc}") from exc

    async def search_similar(
        self,
        embedding: list[float],
        filters: SearchFilters,
    ) -> list[InformalEntry]:
        """
        Run pgvector cosine similarity search with topic + geo metadata pre-filters.
        Calls the `match_informal_entries` Supabase RPC (defined in DB migration).
        Returns top-K results sorted by similarity descending.
        """
        try:
            params = {
                "query_embedding": embedding,
                "match_count": filters.top_k,
                "min_trust": filters.min_trust_score,
                "filter_topic_tags": filters.topic_tags if filters.topic_tags else None,
                "filter_geo_tags": filters.geo_tags if filters.geo_tags else None,
            }
            response = await self.client.rpc("match_informal_entries", params).execute()
            return [InformalEntry.model_validate(row) for row in (response.data or [])]
        except Exception as exc:
            logger.error(
                "search_similar_failed",
                module="repositories",
                operation="search_similar",
                top_k=filters.top_k,
                error=str(exc),
            )
            raise RepositoryError(f"pgvector similarity search failed: {exc}") from exc

    async def soft_delete(self, entry_id: UUID) -> None:
        """Set is_active=False on the entry. Never hard-delete."""
        try:
            await (
                self.client.table("informal_news_entries")
                .update({"is_active": False})
                .eq("id", str(entry_id))
                .execute()
            )
            logger.info(
                "informal_entry_soft_deleted",
                module="repositories",
                operation="soft_delete",
                entry_id=str(entry_id),
            )
        except Exception as exc:
            logger.error(
                "soft_delete_failed",
                module="repositories",
                operation="soft_delete",
                entry_id=str(entry_id),
                error=str(exc),
            )
            raise RepositoryError(f"Failed to soft-delete entry {entry_id}: {exc}") from exc

    async def add_topic_association(
        self,
        entry_id: UUID,
        topic: str,
        relevance_score: float,
        added_by: str,
    ) -> None:
        """Upsert a row in entry_topics linking an entry to a topic."""
        payload = {
            "entry_id": str(entry_id),
            "topic": topic,
            "relevance_score": relevance_score,
            "added_by": added_by,
        }
        try:
            await (
                self.client.table("entry_topics")
                .upsert(payload, on_conflict="entry_id,topic")
                .execute()
            )
            logger.info(
                "topic_association_added",
                module="repositories",
                operation="add_topic_association",
                entry_id=str(entry_id),
                topic=topic,
            )
        except Exception as exc:
            logger.error(
                "add_topic_association_failed",
                module="repositories",
                operation="add_topic_association",
                entry_id=str(entry_id),
                topic=topic,
                error=str(exc),
            )
            raise RepositoryError(
                f"Failed to add topic association for entry {entry_id}: {exc}"
            ) from exc
