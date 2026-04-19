import hashlib
from datetime import datetime
from app.core.logging import get_logger
from app.repositories.sqs import SQSRepository
from app.config import settings

logger = get_logger(__name__)


class IntentLockError(Exception):
    """Raised when intent lock acquisition fails."""
    pass


from contextlib import asynccontextmanager

class IntentLock:
    """
    Publishes a sentinel SQS message to claim an intent lock.
    A second agent attempting the same search within the 5-minute
    deduplication window will be deduped by SQS FIFO.
    """

    def __init__(self, sqs_repo: SQSRepository):
        self.sqs_repo = sqs_repo

    def _get_queue_url(self, topic: str) -> str:
        """Map topic to the correct enrichment queue URL."""
        attr_name = f"sqs_enrich_{topic}_url"
        url = getattr(settings, attr_name, settings.sqs_requests_queue_url) # fallback
        return url

    @asynccontextmanager
    async def acquire(self, group_id: str):
        """
        Attempt to acquire the intent lock for the given topic/geo/year combination.
        Returns the SQS MessageId.
        
        Using SQS FIFO deduplication as a locking mechanism.
        Yields True if successful, False if acquisition failed (though currently we treat all successful publishes as locked).
        """
        # Parse group_id (topic#geo#year)
        parts = group_id.split("#")
        topic = parts[0] if len(parts) > 0 else "regional"
        geo = parts[1] if len(parts) > 1 else "india"
        year = parts[2] if len(parts) > 2 else str(datetime.utcnow().year)
        
        queue_url = self._get_queue_url(topic)
        
        # We use a 5-minute window for the deduplication ID to match SQS FIFO limits.
        # This prevents two searches for the same intent within 5 minutes.
        now_ts = int(datetime.utcnow().timestamp() // 300) * 300
        dedup_seed = f"{group_id}#{now_ts}"
        deduplication_id = hashlib.sha256(dedup_seed.encode()).hexdigest()
        
        msg_id = None
        try:
            msg_id = await self.sqs_repo.publish_message(
                queue_url=queue_url,
                message_body=f"INTENT_LOCK:{group_id}",
                message_group_id=group_id,
                deduplication_id=deduplication_id
            )
            logger.info("intent_lock_acquired", group_id=group_id, msg_id=msg_id)
            yield True
        except Exception as e:
            logger.warning("intent_lock_acquisition_failed", group_id=group_id, error=str(e))
            # In context manager mode, we yield False instead of raising if we want to skip
            # But the original code raised IntentLockError. Let's raise if it's a real SQS error.
            # Actually, per the usage in on_demand.py and base_agent.py:
            # if not locked: return
            # So we should yield False on failure.
            yield False
        finally:
            if msg_id:
                # Release is a noop for SQS FIFO locks sender-side
                # The lock is essentially held until the 5-min dedup window expires
                # or until a consumer processes and deletes the message.
                pass

    async def release(self, topic: str, message_id: str) -> None:
        """
        In this SQS-based model, 'release' is essentially acknowledging the message
        if we were polling. For the synchronous on-demand path, we don't have 
        a receipt handle to delete. Proactive agents will handle their own lifecycle.
        """
        logger.debug("intent_lock_release_noop", topic=topic, message_id=message_id)
        pass
