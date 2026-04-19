class MatchingEngineError(Exception):
    """Base exception for all matching engine errors."""


# Message / Queue
class InvalidMessageError(MatchingEngineError):
    """SQS message failed schema validation."""
class InjectionAttemptError(MatchingEngineError):
    """Input contains a suspected prompt-injection pattern."""
class MessageAcknowledgementError(MatchingEngineError):
    """Failed to delete / acknowledge an SQS message."""


# Repository
class RepositoryError(MatchingEngineError):
    """Generic repository-level error (DB, queue, external API)."""
class RecordNotFoundError(RepositoryError):
    """Expected record was not found in the data store."""
class DuplicateRecordError(RepositoryError):
    """Attempt to insert a record that already exists."""
class OptimisticLockError(RepositoryError):
    """Version mismatch — record was modified by another process."""


# External Services
class TavilyError(MatchingEngineError):
    """Tavily API call failed."""
class LLMError(MatchingEngineError):
    """LLM API call failed (Gemini)."""
class EmbeddingError(LLMError):
    """Embedding generation failed."""
class ChatCompletionError(LLMError):
    """Chat completion call failed."""
# Backward-compatible alias
OpenAIError = LLMError
class SQSError(MatchingEngineError):
    """AWS SQS operation failed."""
class SNSError(MatchingEngineError):
    """AWS SNS publish failed."""


# MCP / Tool Layer
class UnknownToolError(MatchingEngineError):
    """LLM requested a tool that is not in the registered tool registry."""
class ToolGuardrailError(MatchingEngineError):
    """MCP tool call rejected by guardrail validation."""
class RateLimitExceeded(MatchingEngineError):
    """A rate limit (Tavily, LLM, etc.) has been exceeded."""


# Pipeline
class PipelineError(MatchingEngineError):
    """Error during the matching pipeline execution."""
class InsufficientResultsError(PipelineError):
    """RAG results did not meet sufficiency threshold and on-demand is not available."""
class WriteRecommendationError(PipelineError):
    """Failed to write recommendations to Supabase."""

# Crawler
class CrawlAgentError(MatchingEngineError):
    """A crawler agent encountered an unrecoverable error."""
class IntentLockError(MatchingEngineError):
    """Could not acquire SQS-based intent lock for deduplication."""
