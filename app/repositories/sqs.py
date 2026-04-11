"""
SQSRepository — SQS polling, message acknowledgement, and publishing.
Handles both the requests.fifo queue (inbound) and enrichment queues (outbound).
"""

import boto3
from mypy_boto3_sqs import SQSClient

from app.repositories.base import BaseRepository


class SQSMessage:
    """Placeholder — full model will be defined in Phase 2."""


class SQSRepository(BaseRepository):
    def __init__(self, client: "SQSClient") -> None:
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
        """
        # TODO: implement
        raise NotImplementedError

    async def delete_message(self, queue_url: str, receipt_handle: str) -> None:
        """Acknowledge and delete a processed message from SQS."""
        # TODO: implement
        raise NotImplementedError

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
        # TODO: implement
        raise NotImplementedError
