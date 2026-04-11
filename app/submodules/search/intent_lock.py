"""
SQS-based intent lock — prevents duplicate searches for the same intent.
Uses FIFO MessageGroupId serialization instead of Redis distributed locks.

MessageGroupId format: "{topic}#{geo_normalized}#{year}"
e.g., "floods#kerala#2025"

SQS serializes messages with the same group ID, ensuring only one agent
processes a given intent at a time.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


class IntentLock:
    """
    Publishes a sentinel SQS message to claim an intent lock.
    A second agent attempting the same search sees the in-flight message
    and backs off (FIFO ordering guarantees serialization).
    """

    async def acquire(self, topic: str, geo: str, year: int) -> str:
        """
        Attempt to acquire the intent lock for the given topic/geo/year combination.
        Returns the SQS MessageId of the lock message.
        Raises IntentLockError if acquisition fails.
        """
        # TODO: implement (Phase 7)
        raise NotImplementedError

    async def release(self, queue_url: str, receipt_handle: str) -> None:
        """Release the intent lock by deleting the sentinel message."""
        # TODO: implement (Phase 7)
        raise NotImplementedError
