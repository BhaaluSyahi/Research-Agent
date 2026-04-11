"""
SQSRepository — SQS polling, message acknowledgement, and publishing.
Handles both the requests.fifo queue (inbound) and enrichment queues (outbound).
"""

import asyncio
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from app.core.exceptions import SQSError
from app.core.logging import get_logger
from app.repositories.base import BaseRepository

if TYPE_CHECKING:
    from mypy_boto3_sqs import SQSClient
else:
    SQSClient = Any

logger = get_logger(__name__)


class SQSMessage(BaseModel):
    """Pydantic model for an incoming SQS message."""
    body: str
    receipt_handle: str
    message_id: str
    message_group_id: Optional[str] = None
    attributes: dict[str, Any] = {}


class SQSRepository(BaseRepository):
    def __init__(self, client: SQSClient) -> None:
        self.client = client

    async def poll_messages(
        self,
        queue_url: str,
        max_messages: int = 1,
        wait_time_seconds: int = 20,
    ) -> list[SQSMessage]:
        """
        Long-poll SQS for up to max_messages messages.
        Returns an empty list if the queue is empty within wait_time_seconds.
        Uses run_in_executor for the synchronous boto3 call.
        """
        loop = asyncio.get_running_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=max_messages,
                    WaitTimeSeconds=wait_time_seconds,
                    MessageAttributeNames=["All"],
                    AttributeNames=["All"],
                ),
            )

            messages = response.get("Messages", [])
            typed_messages = []
            for msg in messages:
                attributes = msg.get("Attributes", {})
                typed_messages.append(
                    SQSMessage(
                        body=msg.get("Body", ""),
                        receipt_handle=msg.get("ReceiptHandle", ""),
                        message_id=msg.get("MessageId", ""),
                        message_group_id=attributes.get("MessageGroupId"),
                        attributes=attributes,
                    )
                )

            if typed_messages:
                logger.debug(
                    "sqs_messages_polled",
                    module="repositories",
                    operation="poll_messages",
                    count=len(typed_messages),
                    queue_url=queue_url,
                )
            return typed_messages

        except Exception as exc:
            logger.error(
                "sqs_poll_failed",
                module="repositories",
                operation="poll_messages",
                queue_url=queue_url,
                error=str(exc),
            )
            raise SQSError(f"Failed to poll SQS messages from {queue_url}: {exc}") from exc

    async def delete_message(self, queue_url: str, receipt_handle: str) -> None:
        """Acknowledge and delete a processed message from SQS."""
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: self.client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle,
                ),
            )
            logger.debug(
                "sqs_message_deleted",
                module="repositories",
                operation="delete_message",
                queue_url=queue_url,
            )
        except Exception as exc:
            logger.error(
                "sqs_delete_failed",
                module="repositories",
                operation="delete_message",
                queue_url=queue_url,
                error=str(exc),
            )
            # Re-wrap as repo exception
            raise SQSError(f"Failed to delete SQS message: {exc}") from exc

    async def publish_message(
        self,
        queue_url: str,
        message_body: str,
        message_group_id: str,
        deduplication_id: str,
    ) -> str:
        """
        Publish a message to a FIFO queue.
        Returns the SQS MessageId.
        message_group_id format: "{topic}#{geo_normalized}#{year}"
        """
        loop = asyncio.get_running_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=message_body,
                    MessageGroupId=message_group_id,
                    MessageDeduplicationId=deduplication_id,
                ),
            )
            message_id = response.get("MessageId", "")
            logger.info(
                "sqs_message_published",
                module="repositories",
                operation="publish_message",
                queue_url=queue_url,
                message_id=message_id,
                group_id=message_group_id,
            )
            return message_id
        except Exception as exc:
            logger.error(
                "sqs_publish_failed",
                module="repositories",
                operation="publish_message",
                queue_url=queue_url,
                error=str(exc),
            )
            raise SQSError(f"Failed to publish SQS message to {queue_url}: {exc}") from exc
