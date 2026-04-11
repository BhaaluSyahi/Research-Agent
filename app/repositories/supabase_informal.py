"""
SupabaseInformalRepository — CRUD for the informal knowledge base tables.
Owns: informal_news_entries, entry_topics.
"""

from uuid import UUID

from supabase import AsyncClient

from app.repositories.base import BaseRepository


class InformalEntry:
    """Placeholder — full model will be defined in Phase 2."""


class InformalEntryCreate:
    """Placeholder — full model will be defined in Phase 2."""


class SearchFilters:
    """Placeholder — full model will be defined in Phase 2."""


class SupabaseInformalRepository(BaseRepository):
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def get_by_content_hash(self, content_hash: str) -> InformalEntry | None:
        """Return an entry matching the SHA256 content hash, or None."""
        # TODO: implement
        raise NotImplementedError

    async def upsert_entry(self, entry: InformalEntryCreate) -> InformalEntry:
        """
        Insert or update an informal knowledge entry.
        Uses optimistic locking (version field) before update.
        content_hash is the dedup key.
        """
        # TODO: implement
        raise NotImplementedError

    async def search_similar(
        self,
        embedding: list[float],
        filters: SearchFilters,
    ) -> list[InformalEntry]:
        """
        Run pgvector cosine similarity search with topic + geo metadata pre-filters.
        Returns top-K results sorted by similarity descending.
        """
        # TODO: implement
        raise NotImplementedError

    async def soft_delete(self, entry_id: UUID) -> None:
        """Set is_active=False on the entry. Never hard-delete."""
        # TODO: implement
        raise NotImplementedError

    async def add_topic_association(
        self,
        entry_id: UUID,
        topic: str,
        relevance_score: float,
        added_by: str,
    ) -> None:
        """Upsert a row in entry_topics linking an entry to a topic."""
        # TODO: implement
        raise NotImplementedError
