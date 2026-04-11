"""Unit tests for IntentLock."""

import pytest
from app.submodules.search.intent_lock import IntentLock, IntentLockError


@pytest.mark.asyncio
async def test_intent_lock_acquire_success(mocker):
    mock_sqs_repo = mocker.AsyncMock()
    mock_sqs_repo.publish_message.return_value = "msg-123"
    
    lock = IntentLock(mock_sqs_repo)
    msg_id = await lock.acquire(topic="floods", geo="Kerala", year=2025)
    
    assert msg_id == "msg-123"
    mock_sqs_repo.publish_message.assert_called_once()
    
    # Check that MessageGroupId and DeduplicationId are present
    args, kwargs = mock_sqs_repo.publish_message.call_args
    assert kwargs["message_group_id"] == "floods#Kerala#2025"
    assert "deduplication_id" in kwargs


@pytest.mark.asyncio
async def test_intent_lock_acquire_failure(mocker):
    mock_sqs_repo = mocker.AsyncMock()
    mock_sqs_repo.publish_message.side_effect = Exception("SQS Down")
    
    lock = IntentLock(mock_sqs_repo)
    with pytest.raises(IntentLockError, match="Failed to acquire intent lock"):
        await lock.acquire(topic="floods", geo="Kerala", year=2025)
