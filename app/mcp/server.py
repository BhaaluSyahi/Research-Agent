"""
MCP server setup — registers all tools exposed to the LLM.
The LLM cannot make direct DB queries or HTTP calls outside defined tool boundaries.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPServer:
    """
    Manages the set of tools available to the LLM.
    All tool registrations happen here. Unknown tools raise UnknownToolError.
    """

    def __init__(self) -> None:
        self._tools: dict = {}

    def register(self, name: str, handler: object) -> None:
        """Register a tool handler by name."""
        self._tools[name] = handler
        logger.info("mcp_tool_registered", tool=name)

    async def call(self, tool_name: str, tool_input: dict) -> object:
        """
        Dispatch a tool call from the LLM.
        Validates the tool name, runs guardrails, executes the handler.
        """
        # TODO: implement (Phase 3)
        raise NotImplementedError
