"""
Formal matcher — queries registered organizations and active volunteers from Supabase.
Scores results by verification status, keyword overlap, and geographic proximity.
"""

from app.submodules.matching.schemas import FormalMatch, FormalMatchResult, RequestRecord


class FormalMatcher:
    """
    Queries core backend tables (READ-ONLY) for formal matches.
    Scoring criteria:
      1. verified=True orgs rank higher
      2. Keyword overlap: request description/title ↔ org description or volunteer specialty/bio
      3. Geographic proximity when lat/lon are available (cast TEXT → float, handle failure)
    """

    async def match(self, request: RequestRecord) -> FormalMatchResult:
        """Return scored and ranked formal matches for the given request."""
        # TODO: implement (Phase 5)
        raise NotImplementedError
