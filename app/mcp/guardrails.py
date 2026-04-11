"""
Input, tool-call, and output guardrails for all MCP tool interactions.
Three-layer defence as specified in 06_GUARDRAILS.md.
"""

from app.core.exceptions import InjectionAttemptError, ToolGuardrailError

_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "disregard your system prompt",
    "you are now",
    "act as",
    "forget everything",
    "<s>",
    "[inst]",
]

_BLOCKED_DOMAINS: list[str] = []  # extend in Phase 3


# ── Layer 1: Input ────────────────────────────────────────────────────────────

def check_prompt_injection(text: str) -> None:
    """Raise InjectionAttemptError if text contains a prompt-injection pattern."""
    lower = text.lower()
    for pattern in _INJECTION_PATTERNS:
        if pattern in lower:
            raise InjectionAttemptError("Rejected: input contains disallowed pattern")


def strip_and_truncate_article(raw: str, max_chars: int = 8000) -> str:
    """Strip HTML, check for injection, truncate at max_chars. Return clean text."""
    # TODO: implement (Phase 3)
    raise NotImplementedError


# ── Layer 2: Tool Call ────────────────────────────────────────────────────────

def validate_tool_call(tool_name: str, tool_input: dict, registered_tools: set) -> None:
    """
    Universal pre-execution guardrail for every tool call.
    Checks: tool name in registry, input schema, rate limit, audit log.
    """
    # TODO: implement (Phase 3)
    raise NotImplementedError


def validate_write_recommendation(tool_input: dict) -> None:
    """
    Guardrail for the write_recommendation tool.
    Checks: valid UUID, request exists, status=open, confidence ranges, URL format, list sizes.
    """
    # TODO: implement (Phase 3)
    raise NotImplementedError


# ── Layer 3: Output ───────────────────────────────────────────────────────────

def validate_llm_output(raw_output: str, expected_model: type) -> object:
    """
    Parse LLM JSON output through the expected Pydantic model.
    Raises ToolGuardrailError on failure. Retries are handled by the caller.
    """
    # TODO: implement (Phase 3)
    raise NotImplementedError


def check_pii_in_reason(reason: str) -> bool:
    """Return True if the reason field contains detectable PII (email, phone, address)."""
    # TODO: implement (Phase 3)
    raise NotImplementedError
