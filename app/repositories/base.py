"""
Abstract base class for all repository implementations.
Every repository must inherit from BaseRepository and accept its client via constructor.
No business logic lives here — only the shared interface contract.
"""

from abc import ABC


class BaseRepository(ABC):
    """
    Base repository.
    Subclasses must accept their external client via __init__ (constructor injection).
    They must never use global state or call os.getenv().
    All public methods must be async and use typed signatures (Pydantic models in/out).
    Failures must be raised as custom exceptions from app.core.exceptions — never
    let raw client exceptions bubble up to callers.
    """
