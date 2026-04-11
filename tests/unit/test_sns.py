"""Unit tests for SNSRepository."""

import pytest
from app.core.exceptions import SNSError
from app.repositories.sns import SNSRepository


@pytest.mark.asyncio
async def test_publish_to_router(mocker) -> None:
    mock_boto_client = mocker.MagicMock()
    repo = SNSRepository(mock_boto_client)
    mock_boto_client.publish.return_value = {"MessageId": "sns-id"}

    attributes = {"topic": "floods", "priority": 1}
    mid = await repo.publish_to_router("arn", "message", attributes=attributes)

    assert mid == "sns-id"
    mock_boto_client.publish.assert_called_once()
    _, kwargs = mock_boto_client.publish.call_args
    assert kwargs["MessageAttributes"]["topic"]["StringValue"] == "floods"
    assert kwargs["MessageAttributes"]["priority"]["StringValue"] == "1"


@pytest.mark.asyncio
async def test_sns_error_wrapping(mocker) -> None:
    mock_boto_client = mocker.MagicMock()
    repo = SNSRepository(mock_boto_client)
    mock_boto_client.publish.side_effect = Exception("SNS Down")

    with pytest.raises(SNSError):
        await repo.publish_to_router("arn", "msg")
