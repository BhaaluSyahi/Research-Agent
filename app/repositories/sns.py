"""
SNSRepository — publishes to the topic_router SNS topic for fan-out enrichment dispatch.
"""

import asyncio
from typing import TYPE_CHECKING, Any, Optional

from app.core.exceptions import SNSError
from app.core.logging import get_logger
from app.repositories.base import BaseRepository

if TYPE_CHECKING:
    from mypy_boto3_sns import SNSClient
else:
    SNSClient = Any

logger = get_logger(__name__)


class SNSRepository(BaseRepository):
    def __init__(self, client: SNSClient) -> None:
        self.client = client

    async def publish_to_router(
        self,
        topic_arn: str,
        message: str,
        subject: str = "enrichment_request",
        attributes: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Publish an enrichment request to the SNS topic_router topic.
        Returns the SNS MessageId.
        Subscription filter attributes route the message to the correct enrich.*.fifo queue.
        Uses run_in_executor for the synchronous boto3 call.
        """
        # Convert attributes to SNS format
        message_attributes = {}
        if attributes:
            for key, value in attributes.items():
                if isinstance(value, str):
                    message_attributes[key] = {"DataType": "String", "StringValue": value}
                elif isinstance(value, (int, float)):
                    message_attributes[key] = {"DataType": "Number", "StringValue": str(value)}
                # Add more types if needed

        loop = asyncio.get_running_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.publish(
                    TopicArn=topic_arn,
                    Message=message,
                    Subject=subject,
                    MessageAttributes=message_attributes,
                ),
            )
            message_id = response.get("MessageId", "")
            logger.info(
                "sns_published",
                module="repositories",
                operation="publish_to_router",
                message_id=message_id,
                topic_arn=topic_arn,
            )
            return message_id
        except Exception as exc:
            logger.error(
                "sns_publish_failed",
                module="repositories",
                operation="publish_to_router",
                topic=topic_arn,
                error=str(exc),
            )
            raise SNSError(f"Failed to publish to SNS topic {topic_arn}: {exc}") from exc
