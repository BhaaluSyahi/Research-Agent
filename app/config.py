"""
Application configuration loaded from environment variables via pydantic-settings.
All env vars must be defined here. No os.getenv() calls elsewhere in the codebase.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_key: str  # service role key — never the anon key

    # AWS
    aws_region: str = "ap-south-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    sqs_requests_queue_url: str
    sns_topic_router_arn: str

    # SQS enrichment queues (one per topic)
    sqs_enrich_floods_url: str = ""
    sqs_enrich_drought_url: str = ""
    sqs_enrich_healthcare_url: str = ""
    sqs_enrich_disaster_url: str = ""
    sqs_enrich_welfare_url: str = ""
    sqs_enrich_education_url: str = ""
    sqs_enrich_livelihood_url: str = ""
    sqs_enrich_environment_url: str = ""
    sqs_enrich_regional_url: str = ""

    # Gemini
    gemini_api_key: str
    gemini_embedding_model: str = "text-embedding-004"
    gemini_chat_model: str = "gemini-2.0-flash"

    # Tavily
    tavily_api_key: str

    # Matching thresholds
    dry_run: bool = False
    rag_sufficiency_min_results: int = 3
    rag_sufficiency_min_score: float = 0.75
    rag_top_k: int = 20
    rag_rerank_top_n: int = 5

    # Crawler
    crawler_default_frequency_hours: int = 6
    crawler_max_articles_per_run: int = 20

    # Cost controls (per pipeline run)
    max_llm_calls_per_request: int = 5
    max_tavily_calls_per_request: int = 10
    max_embedding_calls_per_request: int = 15

    # Cost controls (per crawler run)
    max_articles_per_crawl_run: int = 20
    max_llm_calls_per_crawl_run: int = 25
    max_tavily_calls_per_crawl_run: int = 5

    # Global rate limits
    max_tavily_calls_per_minute: int = 10

    # SQS polling
    sqs_max_messages: int = 1
    sqs_wait_time_seconds: int = 20
    sqs_visibility_timeout: int = 300

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()  # type: ignore[call-arg]
