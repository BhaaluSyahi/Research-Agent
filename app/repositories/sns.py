"""
SNSRepository — publishes to the topic_router SNS topic for fan-out enrichment dispatch.
"""

from app.repositories.base import BaseRepository


class SNSRepository(BaseRepository):
    def __init__(self, client: object) -> None:
        self.client = client  # boto3 SNS client

    async def publish_to_router(
        self,
        topic_arn: str,
        message: str,
        subject: str = "enrichment_request",
        attributes: dict | None = None,
    ) -> str:
        """
        Publish an enrichment request to the SNS topic_router topic.
        Returns the SNS MessageId.
        Subscription filter attributes route the message to the correct enrich.*.fifo queue.
        """
        # TODO: implement
        raise NotImplementedError
