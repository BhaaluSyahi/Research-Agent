import re
from typing import Any, Optional, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel, ValidationError

from app.core.exceptions import (
    InjectionAttemptError,
    RecordNotFoundError,
    ToolGuardrailError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "disregard your system prompt",
    "you are now",
    "act as",
    "forget everything",
    "<s>",
    "[inst]",
] # Claude code is no better themselves so...

_BLOCKED_DOMAINS: list[str] = [
    "doubleclick.net",
    "googleadservices.com",
    "facebook.com/ads",
] # Will reallistically need to add tonnes more

_PII_PATTERNS = [
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",  # Email
    r"\+?(\d{1,3})?[-.\s]?(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})",  # Phone (US/Intl general)
] # Also need to add more

# Layer 1: Input
def check_prompt_injection(text: str) -> None:
    """Raise InjectionAttemptError if text contains a prompt-injection pattern."""
    lower = text.lower()
    for pattern in _INJECTION_PATTERNS:
        if pattern in lower:
            raise InjectionAttemptError(f"Rejected: input contains disallowed pattern '{pattern}'")


def strip_and_truncate_article(raw: str, max_chars: int = 8000) -> str:
    """Strip HTML, check for injection, truncate at max_chars. Return clean text."""
    # Simple HTML strip (regex)
    clean = re.sub(r"<[^>]*>", "", raw)
    
    # Check injection on the result
    check_prompt_injection(clean)
    
    # Truncate
    truncated = clean[:max_chars]
    
    if len(truncated) < 200:
        logger.warning("article_too_short", length=len(truncated))
        # We don't raise here, but the caller (crawler) should skip if length < 200
        
    return truncated


# Layer 2: Tool Call
def validate_tool_call(tool_name: str, tool_input: dict, registered_tools: set[str]) -> None:
    """
    Universal pre-execution guardrail for every tool call.
    Checks: tool name in registry.
    Input schema validation is handled by the dispatcher (Pydantic).
    """
    if tool_name not in registered_tools:
        raise ToolGuardrailError(f"Unknown tool: {tool_name}")


async def validate_write_recommendation(
    tool_input: dict, 
    get_request_func: Any
) -> None:
    """
    Guardrail for the write_recommendation tool.
    Checks: valid UUID, request exists, status=open, confidence ranges, URL format, list sizes.
    """
    request_id = tool_input.get("request_id")
    try:
        UUID(str(request_id))
    except ValueError:
        raise ToolGuardrailError(f"Invalid request_id format: {request_id}")

    # Chained existence check
    request = await get_request_func(request_id)
    if not request:
        raise RecordNotFoundError(f"Request {request_id} not found in database")
    
    if request.status != "open":
        raise ToolGuardrailError(f"Cannot write recommendations to a {request.status} request")

    # Confidence check
    for match in tool_input.get("formal_matches", []):
        conf = match.get("confidence", 0.0)
        if not (0.0 <= conf <= 1.0):
            raise ToolGuardrailError(f"Formal match confidence {conf} out of range [0, 1]")

    # List sizes
    if len(tool_input.get("formal_matches", [])) > 10:
        tool_input["formal_matches"] = tool_input["formal_matches"][:10]
    if len(tool_input.get("informal_matches", [])) > 10:
        tool_input["informal_matches"] = tool_input["informal_matches"][:10]


# Layer 3: Output
def validate_llm_output(raw_output: str, expected_model: Type[T]) -> T:
    """
    Parse LLM JSON output through the expected Pydantic model.
    Raises ToolGuardrailError on failure.
    """
    try:
        return expected_model.model_validate_json(raw_output)
    except ValidationError as e:
        logger.warning("llm_output_validation_failed", error=str(e), raw=raw_output[:500])
        raise ToolGuardrailError(f"LLM output failed schema validation: {e}")


def check_pii_in_reason(reason: str) -> bool:
    """Return True if the reason field contains detectable PII (email, phone)."""
    for pattern in _PII_PATTERNS:
        if re.search(pattern, reason):
            return True
    return False
