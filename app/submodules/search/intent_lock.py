import hashlib
from datetime import datetime
from app.core.logging import get_logger
from app.repositories.sqs import SQSRepository
from app.config import settings

logger = get_logger(__name__)


class IntentLockError(Exception):
    """Raised when intent lock acquisition fails."""
    pass


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

    async def acquire(self, topic: str, geo: str, year: int) -> str:
        """
        Attempt to acquire the intent lock for the given topic/geo/year combination.
        Returns the SQS MessageId.
        
        Using SQS FIFO deduplication as a locking mechanism.
        """
        queue_url = self._get_queue_url(topic)
        group_id = f"{topic}#{geo}#{year}"
        
        # We use a 5-minute window for the deduplication ID to match SQS FIFO limits.
        # This prevents two searches for the same intent within 5 minutes.
        now_ts = int(datetime.utcnow().timestamp() // 300) * 300
        dedup_seed = f"{group_id}#{now_ts}"
        deduplication_id = hashlib.sha256(dedup_seed.encode()).hexdigest()
        
        try:
            msg_id = await self.sqs_repo.publish_message(
                queue_url=queue_url,
                message_body=f"INTENT_LOCK:{group_id}",
                message_group_id=group_id,
                deduplication_id=deduplication_id
            )
            return msg_id
        except Exception as e:
            logger.error("intent_lock_acquisition_failed", topic=topic, geo=geo, error=str(e))
            raise IntentLockError(f"Failed to acquire intent lock: {e}")

    async def release(self, topic: str, message_id: str) -> None:
        """
        In this SQS-based model, 'release' is essentially acknowledging the message
        if we were polling. For the synchronous on-demand path, we don't have 
        a receipt handle to delete. Proactive agents will handle their own lifecycle.
        """
        logger.debug("intent_lock_release_noop", topic=topic, message_id=message_id)
        pass
