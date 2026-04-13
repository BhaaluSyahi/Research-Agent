"""
MCP server setup — registers all tools exposed to the LLM.
"""

from typing import Any, Callable, Dict
from app.core.exceptions import ToolGuardrailError, UnknownToolError
from app.core.logging import get_logger
from app.mcp.guardrails import validate_tool_call, check_prompt_injection

logger = get_logger(__name__)


class MCPServer:
    """
    Manages the set of tools available to the LLM.
    Ensures every tool call passes through guardrails before execution.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Callable] = {} # The best we can do to simulate private members

    def register(self, name: str, handler: Callable) -> None:
        """Register a tool handler by name."""
        self._tools[name] = handler
        logger.info("mcp_tool_registered", tool=name)

    async def call(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        # 1. Global registry check
        validate_tool_call(tool_name, tool_input, set(self._tools.keys()))
        
        # 2. Global input guardrail: check all string values for prompt injection
        self._deep_check_injection(tool_input)

        handler = self._tools[tool_name]
        
        try:
            logger.info("mcp_tool_call", tool=tool_name, input_keys=list(tool_input.keys()))
            result = await handler(**tool_input)
            return result
        except TypeError as e:
            # Handle mismatch between tool_input and handler arguments
            raise ToolGuardrailError(f"Tool '{tool_name}' received invalid arguments: {e}")
        except Exception as e:
            logger.error("mcp_tool_execution_failed", tool=tool_name, error=str(e))
            raise e

    def _deep_check_injection(self, data: Any) -> None:
        """Recursively check all strings in a nested structure for injection patterns."""
        if isinstance(data, str):
            check_prompt_injection(data)
        elif isinstance(data, dict):
            for v in data.values():
                self._deep_check_injection(v)
        elif isinstance(data, list):
            for v in data:
                self._deep_check_injection(v)
