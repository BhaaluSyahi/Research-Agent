"""
Pydantic schemas for the matching submodule.

Includes:
  - Core backend read models (verbatim from 03_SCHEMA.md — do not redefine elsewhere)
  - Match result models produced by this service
  - The final RecommendationPayload written to requests.recommendations (JSONB)
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


# ── Core Backend Read Models (READ ONLY — copied verbatim from 03_SCHEMA.md) ──


class UserRecord(BaseModel):
    id: UUID
    email: str
    role: Literal["employee", "volunteer"]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class VolunteerProfileRecord(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    phone: Optional[str] = None
    latitude: Optional[str] = None       # TEXT in DB — cast to float yourself when needed
    longitude: Optional[str] = None      # TEXT in DB — cast to float yourself when needed
    specialty: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class OrganizationRecord(BaseModel):
    id: UUID
    name: str
    type: Literal["village", "ngo", "other"]
    description: Optional[str] = None
    verified: bool
    status: Literal["draft", "pending", "registered", "rejected"]
    created_by: UUID
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class OrganizationMembershipRecord(BaseModel):
    id: UUID
    organization_id: UUID
    volunteer_id: UUID
    role: Literal["admin", "subadmin", "member"]
    added_by: UUID
    joined_at: datetime
    is_active: bool


class RequestRecord(BaseModel):
    id: UUID
    title: str
    description: str
    location_type: Literal["online", "location"]
    location_text: Optional[str] = None
    latitude: Optional[str] = None       # TEXT in DB
    longitude: Optional[str] = None      # TEXT in DB
    issuer_type: Literal["volunteer", "organization"]
    issuer_id: UUID
    status: Literal["open", "closed", "deleted"]
    progress_percent: int
    recommendations: Optional[dict] = None    # JSONB — this service writes here
    infoboard: Optional[dict] = None          # JSONB — do not write here
    agent_research_status: Literal["pending", "in_progress", "complete"]
    created_at: datetime
    updated_at: datetime


# ── Matching Result Models (produced by this service) ─────────────────────────


class FormalMatch(BaseModel):
    """A single formal match result (organization or volunteer)."""
    entity_type: Literal["organization", "volunteer"]
    entity_id: UUID
    name: str
    confidence: float            # 0.0 – 1.0
    reason: str                  # Brief explanation of why this entity was matched
    verified: bool = False       # True if org is verified


class FormalMatchResult(BaseModel):
    """Aggregated formal matching output."""
    request_id: UUID
    matches: list[FormalMatch]
    scored_at: datetime


class InformalMatch(BaseModel):
    """A single informal RAG match result from the knowledge base."""
    entry_id: UUID
    title: Optional[str]
    summary: str                 # Always from DB — never LLM-regenerated at recommendation time
    source_url: str
    trust_score: float
    cosine_score: float
    relevance_reason: str        # LLM-generated: why this is relevant to the specific request
    topic_tags: list[str]
    geo_tags: list[str]


class RecommendationPayload(BaseModel):
    """
    Final payload written to requests.recommendations (JSONB).
    This is the canonical output format of the matching pipeline.
    """
    request_id: UUID
    formal_matches: list[FormalMatch]
    informal_matches: list[InformalMatch]
    pipeline_version: str = "1.0"
    on_demand_triggered: bool = False
    generated_at: datetime
