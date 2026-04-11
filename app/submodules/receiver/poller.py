"""
SQS polling loop for the requests.fifo queue.
Continuously polls for new help requests, validates them, and kicks off the matching pipeline.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestPoller:
    """
    Polls the SQS requests.fifo queue in a loop.
    On each message:
      1. Calls validator.validate_sqs_message()
      2. Writes agent_research_status = 'in_progress'
      3. Dispatches to MatchingPipeline (stub in Phase 4, wired in Phase 8)
      4. Deletes message from SQS on success
    Dead-letter: if validation fails, log error and let SQS DLQ handle it.
    """

    async def start(self) -> None:
        """Begin the polling loop. Runs indefinitely until cancelled."""
        # TODO: implement (Phase 4)
        raise NotImplementedError

    async def stop(self) -> None:
        """Gracefully stop the polling loop."""
        # TODO: implement (Phase 4)
        raise NotImplementedError
