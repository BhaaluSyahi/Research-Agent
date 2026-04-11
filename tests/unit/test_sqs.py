"""Unit tests for SQSRepository."""

import pytest
from botocore.exceptions import ClientError

from app.core.exceptions import SQSError
from app.repositories.sqs import SQSRepository


@pytest.mark.asyncio
async def test_poll_messages(mocker) -> None:
    # Mock boto3 SQS client
    mock_boto_client = mocker.MagicMock()
    repo = SQSRepository(mock_boto_client)
    queue_url = "https://sqs.test.url"

    mock_response = {
        "Messages": [
            {
                "Body": '{"test": "data"}',
                "ReceiptHandle": "handle-123",
                "MessageId": "id-123",
                "Attributes": {"MessageGroupId": "group-1"},
            }
        ]
    }
    mock_boto_client.receive_message.return_value = mock_response

    messages = await repo.poll_messages(queue_url)

    assert len(messages) == 1
    assert messages[0].message_id == "id-123"
    assert messages[0].message_group_id == "group-1"
    mock_boto_client.receive_message.assert_called_once()


@pytest.mark.asyncio
async def test_delete_message(mocker) -> None:
    mock_boto_client = mocker.MagicMock()
    repo = SQSRepository(mock_boto_client)
    
    await repo.delete_message("url", "handle")
    mock_boto_client.delete_message.assert_called_once_with(QueueUrl="url", ReceiptHandle="handle")


@pytest.mark.asyncio
async def test_publish_message(mocker) -> None:
    mock_boto_client = mocker.MagicMock()
    repo = SQSRepository(mock_boto_client)
    mock_boto_client.send_message.return_value = {"MessageId": "new-id"}

    mid = await repo.publish_message("url", "body", "group", "dedup")

    assert mid == "new-id"
    mock_boto_client.send_message.assert_called_once_with(
        QueueUrl="url", MessageBody="body", MessageGroupId="group", MessageDeduplicationId="dedup"
    )


@pytest.mark.asyncio
async def test_sqs_error_wrapping(mocker) -> None:
    mock_boto_client = mocker.MagicMock()
    repo = SQSRepository(mock_boto_client)
    
    # Mock a ClientError
    error_response = {'Error': {'Code': 'InternalError', 'Message': 'Broken'}}
    mock_boto_client.receive_message.side_effect = ClientError(error_response, 'ReceiveMessage')

    with pytest.raises(SQSError):
        await repo.poll_messages("url")
