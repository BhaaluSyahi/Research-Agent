"""
SQS polling loop for the requests.fifo queue.
Continuously polls for new help requests, validates them, and kicks off the matching pipeline.
"""

from datetime import datetime
import asyncio
from typing import Optional

from app.core.logging import get_logger
from app.repositories.sqs import SQSRepository
from app.repositories.supabase_formal import SupabaseFormalRepository
from app.submodules.receiver.validator import validate_sqs_message
from app.submodules.matching.pipeline import MatchingPipeline
from app.core.exceptions import InvalidMessageError, ToolGuardrailError

logger = get_logger(__name__)


class RequestPoller:
    """
    Polls the SQS requests.fifo queue in a loop.
    Steps for each message:
      1. Validate via validate_sqs_message()
      2. Set status to 'in_progress' in formal DB
      3. Call MatchingPipeline
      4. Ack/Delete message from SQS
    """

    def __init__(
        self,
        sqs_repo: SQSRepository,
        formal_repo: SupabaseFormalRepository,
        queue_url: str,
        pipeline: MatchingPipeline
    ):
        self.sqs_repo = sqs_repo
        self.formal_repo = formal_repo
        self.queue_url = queue_url
        self.pipeline = pipeline
        self._running = False
        self.last_poll_at: Optional[datetime] = None

    async def start(self) -> None:
        """Begin the polling loop. Runs indefinitely until stop() is called."""
        self._running = True
        logger.info("request_poller_started", queue_url=self.queue_url)

        while self._running:
            try:
                from datetime import datetime
                self.last_poll_at = datetime.utcnow()
                messages = await self.sqs_repo.poll_messages(
                    queue_url=self.queue_url,
                    max_messages=1,
                    wait_time_seconds=20
                )

                if not messages:
                    continue

                for msg in messages:
                    await self._process_message(msg)

            except Exception as e:
                logger.error("poller_loop_error", error=str(e))
                await asyncio.sleep(5)  # Backoff on error

    async def stop(self) -> None:
        """Gracefully stop the polling loop."""
        self._running = False
        logger.info("request_poller_stopping")

    def get_status(self) -> dict:
        """Return status info for monitoring."""
        return {
            "running": self._running,
            "last_poll_at": self.last_poll_at.isoformat() if self.last_poll_at else None
        }

    async def _process_message(self, message) -> None:
        """Internal processing logic for a single SQS message."""
        request_record = None
        try:
            # 1. Validation
            request_record = validate_sqs_message(message.body)
            
            # Silently discard if not open
            if request_record.status != "open":
                logger.info("request_ignored", reason="status_not_open", status=request_record.status)
                await self.sqs_repo.delete_message(self.queue_url, message.receipt_handle)
                return

            logger.info("request_received", request_id=str(request_record.id))

            # 2. Update DB status
            await self.formal_repo.update_request_status(
                request_id=request_record.id,
                agent_research_status="in_progress"
            )

            # 3. Pipeline call
            await self.pipeline.run(request_record)

            # 4. Acknowledge
            await self.sqs_repo.delete_message(self.queue_url, message.receipt_handle)
            logger.info("request_acknowledged", request_id=str(request_record.id))

        except (InvalidMessageError, ToolGuardrailError) as e:
            # Poison pill: ACK/Delete but log as failure
            logger.error("permanent_failure_poison_pill", error=str(e), message_id=message.message_id)
            if request_record:
                await self.formal_repo.update_request_status(
                    request_id=request_record.id,
                    agent_research_status="failed"
                )
            await self.sqs_repo.delete_message(self.queue_url, message.receipt_handle)
            
        except Exception as e:
            # Transient failure: Let SQS retry
            logger.error("transient_processing_failed", error=str(e), message_id=message.message_id)
            if request_record:
                await self.formal_repo.update_request_status(
                    request_id=request_record.id,
                    agent_research_status="pending" # Reset to pending for retry
                )
