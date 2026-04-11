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
from app.core.logging import get_logger
from app.repositories.base import BaseRepository
from app.submodules.matching.schemas import (
    OrganizationRecord,
    RequestRecord,
    VolunteerProfileRecord,
)

logger = get_logger(__name__)


class SupabaseFormalRepository(BaseRepository):
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def get_registered_organizations(self) -> list[OrganizationRecord]:
        """Return all organizations with status='registered'."""
        try:
            response = (
                await self.client.table("organizations")
                .select("*")
                .eq("status", "registered")
                .execute()
            )
            return [OrganizationRecord.model_validate(row) for row in response.data]
        except Exception as exc:
            logger.error(
                "get_registered_organizations_failed",
                module="repositories",
                operation="get_registered_organizations",
                error=str(exc),
            )
            raise RepositoryError(f"Failed to fetch registered organizations: {exc}") from exc

    async def get_active_volunteers(self) -> list[VolunteerProfileRecord]:
        """Return all volunteer profiles where the linked user is active."""
        try:
            # Join volunteer_profiles with users, filtering for is_active=True users
            response = (
                await self.client.table("volunteer_profiles")
                .select("*, users!inner(is_active)")
                .eq("users.is_active", True)
                .execute()
            )
            # Strip the nested users dict before validation — schema doesn't include it
            rows = []
            for row in response.data:
                row_clean = {k: v for k, v in row.items() if k != "users"}
                rows.append(VolunteerProfileRecord.model_validate(row_clean))
            return rows
        except Exception as exc:
            logger.error(
                "get_active_volunteers_failed",
                module="repositories",
                operation="get_active_volunteers",
                error=str(exc),
            )
            raise RepositoryError(f"Failed to fetch active volunteers: {exc}") from exc

    async def get_request_by_id(self, request_id: UUID) -> RequestRecord | None:
        """Fetch a single request row by primary key. Returns None if not found."""
        try:
            response = (
                await self.client.table("requests")
                .select("*")
                .eq("id", str(request_id))
                .maybe_single()
                .execute()
            )
            if response.data is None:
                return None
            return RequestRecord.model_validate(response.data)
        except Exception as exc:
            logger.error(
                "get_request_by_id_failed",
                module="repositories",
                operation="get_request_by_id",
                request_id=str(request_id),
                error=str(exc),
            )
            raise RepositoryError(f"Failed to fetch request {request_id}: {exc}") from exc

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
        payload: dict = {"agent_research_status": agent_research_status}
        if recommendations is not None:
            payload["recommendations"] = recommendations

        try:
            await (
                self.client.table("requests")
                .update(payload)
                .eq("id", str(request_id))
                .execute()
            )
            logger.info(
                "request_status_updated",
                module="repositories",
                operation="update_request_status",
                request_id=str(request_id),
                agent_research_status=agent_research_status,
                has_recommendations=recommendations is not None,
            )
        except Exception as exc:
            logger.error(
                "update_request_status_failed",
                module="repositories",
                operation="update_request_status",
                request_id=str(request_id),
                error=str(exc),
            )
            raise RepositoryError(
                f"Failed to update request status for {request_id}: {exc}"
            ) from exc
