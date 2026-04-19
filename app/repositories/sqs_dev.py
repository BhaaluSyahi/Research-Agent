"""
DevSQSRepository — Simulated SQS repository for dev-mode.
Reads from tests/dev-mode/requests.py instead of AWS.
"""

import asyncio
import json
import uuid
from typing import Any

from app.core.logging import get_logger
from app.repositories.sqs import SQSRepository, SQSMessage
from tests.dev_mode.requests import REQUEST_ARR

logger = get_logger(__name__)


class DevSQSRepository(SQSRepository):
    def __init__(self, *args, **kwargs) -> None:
        # no real client needed
        self.queue = list(REQUEST_ARR)
        logger.info("dev_sqs_repository_initialized", initial_count=len(self.queue))

    async def poll_messages(
        self,
        queue_url: str,
        max_messages: int = 1,
        wait_time_seconds: int = 20,
    ) -> list[SQSMessage]:
        """Simulate polling by yielding one message from the list."""
        if not self.queue:
            # Long poll simulation
            await asyncio.sleep(min(wait_time_seconds, 5))
            return []

        # Take front of queue
        raw_msg = self.queue.pop(0)
        
        # Wrap as SQSMessage
        msg = SQSMessage(
            body=json.dumps(raw_msg),
            receipt_handle=f"dev-receipt-{uuid.uuid4()}",
            message_id=f"dev-msg-{uuid.uuid4()}",
            attributes={"MessageGroupId": raw_msg.get("category", "default")}
        )
        
        logger.info("dev_sqs_message_polled", message_id=msg.message_id, topic=msg.attributes["MessageGroupId"])
        return [msg]

    async def delete_message(self, queue_url: str, receipt_handle: str) -> None:
        """No-op for simulation."""
        logger.info("dev_sqs_message_acknowledged", receipt_handle=receipt_handle)

    async def publish_message(
        self,
        queue_url: str,
        message_body: str,
        message_group_id: str,
        deduplication_id: str,
    ) -> str:
        """Simply log the outgoing message."""
        msg_id = f"dev-out-{uuid.uuid4()}"
        logger.info(
            "dev_sqs_message_published",
            queue_url=queue_url,
            message_id=msg_id,
            group_id=message_group_id
        )
        return msg_id
