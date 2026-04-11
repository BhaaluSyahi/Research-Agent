"""
SQS message validator.
Deserializes SQS message bodies into RequestRecord and performs prompt injection checks.
Uses RequestRecord from app.submodules.matching.schemas — do not define a separate model.
"""

from app.core.exceptions import InjectionAttemptError, InvalidMessageError
from app.submodules.matching.schemas import RequestRecord

_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "disregard your system prompt",
    "you are now",
    "act as",
    "forget everything",
    "<s>",
    "[inst]",
]


def validate_sqs_message(raw_body: str) -> RequestRecord:
    """
    Parse and validate an SQS message body.
    - Deserializes JSON into RequestRecord (raises InvalidMessageError on failure)
    - Checks title and description for prompt injection patterns
    - Returns the validated RequestRecord
    Callers should silently discard messages where status != 'open'.
    """
    # TODO: implement (Phase 4)
    raise NotImplementedError


def _check_prompt_injection(text: str) -> None:
    """Raise InjectionAttemptError if text contains a known prompt-injection pattern."""
    lower = text.lower()
    for pattern in _INJECTION_PATTERNS:
        if pattern in lower:
            raise InjectionAttemptError("Rejected: input contains disallowed pattern")
