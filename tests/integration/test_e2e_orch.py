"""End-to-End Orchestration Test."""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime
from app.submodules.receiver.poller import RequestPoller
from app.submodules.matching.pipeline import MatchingPipeline
from app.submodules.matching.schemas import RequestRecord


@pytest.mark.asyncio
async def test_e2e_orchestration_success(mocker):
    # Mock repositories
    mock_sqs_repo = mocker.AsyncMock()
    mock_formal_repo = mocker.AsyncMock()
    mock_pipeline = mocker.AsyncMock()
    
    queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/requests.fifo"
    poller = RequestPoller(mock_sqs_repo, mock_formal_repo, queue_url, mock_pipeline)
    
    # 1. Mock SQS survey
    request_id = uuid4()
    mock_msg = mocker.Mock()
    mock_msg.body = f'{{"id": "{request_id}", "title": "Help needed", "description": "Flood rescue", "location_type": "location", "issuer_type": "organization", "issuer_id": "{uuid4()}", "status": "open", "progress_percent": 0, "agent_research_status": "pending", "created_at": "2026-04-11T12:00:00Z", "updated_at": "2026-04-11T12:00:00Z"}}'
    mock_msg.receipt_handle = "receipt-123"
    mock_msg.message_id = "msg-123"
    
    mock_sqs_repo.poll_messages.side_effect = [[mock_msg], []] # Poll once then empty
    
    # 2. Run poller for a brief moment
    # We'll manually trigger _process_message to avoid the infinite loop in start()
    await poller._process_message(mock_msg)
    
    # 3. Assertions
    # DB status updated to in_progress
    mock_formal_repo.update_request_status.assert_any_call(
        request_id=request_id,
        agent_research_status="in_progress"
    )
    
    # Pipeline called
    mock_pipeline.run.assert_called_once()
    
    # Message deleted
    mock_sqs_repo.delete_message.assert_called_once_with(queue_url, "receipt-123")


@pytest.mark.asyncio
async def test_e2e_orchestration_poison_pill(mocker):
    from app.core.exceptions import InvalidMessageError
    
    mock_sqs_repo = mocker.AsyncMock()
    mock_formal_repo = mocker.AsyncMock()
    mock_pipeline = mocker.AsyncMock()
    
    poller = RequestPoller(mock_sqs_repo, mock_formal_repo, "url", mock_pipeline)
    
    # Invalid message body
    mock_msg = mocker.Mock()
    mock_msg.body = "INVALID JSON"
    mock_msg.receipt_handle = "receipt-fail"
    mock_msg.message_id = "msg-fail"
    
    await poller._process_message(mock_msg)
    
    # Should delete message (poison pill)
    mock_sqs_repo.delete_message.assert_called_once()
    # pipeline should NOT be called
    mock_pipeline.run.assert_not_called()
