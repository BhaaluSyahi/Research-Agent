"""
SupabaseFormalRepository — READ-ONLY access to core backend tables.
Queries: organizations, volunteer_profiles, requests (read fields only).
Never modifies core backend table structure.

Writable fields on requests:
  - agent_research_status
  - recommendations
"""

from uuid import UUID

from supabase import AsyncClient

from app.core.exceptions import RecordNotFoundError, RepositoryError
from app.repositories.base import BaseRepository
from app.submodules.matching.schemas import (
    OrganizationRecord,
    RequestRecord,
    VolunteerProfileRecord,
)


class SupabaseFormalRepository(BaseRepository):
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def get_registered_organizations(self) -> list[OrganizationRecord]:
        """Return all organizations with status='registered'."""
        # TODO: implement
        raise NotImplementedError

    async def get_active_volunteers(self) -> list[VolunteerProfileRecord]:
        """Return all volunteer profiles where the linked user is active."""
        # TODO: implement
        raise NotImplementedError

    async def get_request_by_id(self, request_id: UUID) -> RequestRecord | None:
        """Fetch a single request row by primary key. Returns None if not found."""
        # TODO: implement
        raise NotImplementedError

    async def update_request_status(
        self,
        request_id: UUID,
        agent_research_status: str,
        recommendations: dict | None = None,
    ) -> None:
        """
        Write agent_research_status (and optionally recommendations) to the requests table.
        Only these two fields may be written — all others are read-only for this service.
        """
        # TODO: implement
        raise NotImplementedError
