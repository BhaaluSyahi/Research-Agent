"""
Validates and deserializes incoming SQS messages from the core backend.
"""

from app.core.exceptions import InvalidMessageError
from app.mcp.guardrails import check_prompt_injection
from app.submodules.matching.schemas import RequestRecord


def validate_sqs_message(raw_body: str) -> RequestRecord:
    """
    Validate and deserialize a raw SQS message body.
    1. Parse through RequestRecord schema
    2. Check title and description for prompt injection
    3. Ensure status is 'open'
    """
    try:
        request = RequestRecord.model_validate_json(raw_body)
    except Exception as e:
        raise InvalidMessageError(f"SQS message failed schema validation: {e}")

    # Injection check on user-provided text fields
    check_prompt_injection(request.title)
    check_prompt_injection(request.description)

    return request
