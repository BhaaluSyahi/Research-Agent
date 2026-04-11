"""
SQS polling loop for the requests.fifo queue.
Continuously polls for new help requests, validates them, and kicks off the matching pipeline.
"""

import asyncio
from typing import Optional

from app.core.logging import get_logger
from app.repositories.sqs import SQSRepository
from app.repositories.supabase_formal import SupabaseFormalRepository
from app.submodules.receiver.validator import validate_sqs_message

logger = get_logger(__name__)


class RequestPoller:
    """
    Polls the SQS requests.fifo queue in a loop.
    Steps for each message:
      1. Validate via validate_sqs_message()
      2. Set status to 'in_progress' in formal DB
      3. [TODO] Call MatchingPipeline
      4. Ack/Delete message from SQS
    """

    def __init__(
        self,
        sqs_repo: SQSRepository,
        formal_repo: SupabaseFormalRepository,
        queue_url: str,
    ):
        self.sqs_repo = sqs_repo
        self.formal_repo = formal_repo
        self.queue_url = queue_url
        self._running = False

    async def start(self) -> None:
        """Begin the polling loop. Runs indefinitely until stop() is called."""
        self._running = True
        logger.info("request_poller_started", queue_url=self.queue_url)

        while self._running:
            try:
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

    async def _process_message(self, message) -> None:
        """Internal processing logic for a single SQS message."""
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

            # 3. [Phase 8] Pipeline call goes here
            # For now, we'll just log and ack
            logger.info("request_processing_stub", request_id=str(request_record.id))

            # 4. Acknowledge
            await self.sqs_repo.delete_message(self.queue_url, message.receipt_handle)
            logger.info("request_acknowledged", request_id=str(request_record.id))

        except Exception as e:
            logger.error("message_processing_failed", error=str(e), message_id=message.message_id)
            # We don't delete here; SQS visibility timeout will expire and it will be retried or DLQ'd
