# Matching Engine Microservice

Production-grade research and matching engine for connecting help requests with NGO resources.

## Features

- **Proactive Search Fleet**: Topic-specific agents that crawl the web for NGO data based on dynamic strategies.
- **On-Demand Enrichment**: Fast-path search triggered when local knowledge is insufficient for a match.
- **Hybrid Matching**: Combines semantic RAG search with metadata-based formal verification.
- **Cost Controls**: Hard limits on LLM and Tavily usage to prevent runaway costs.
- **Structured Logging**: JSON logs for all operations, indexed for observability.
- **Operational Monitoring**: Real-time status endpoints for fleet and pipeline health.

## Tech Stack

- **FastAPI**: Main API framework.
- **Supabase**: PostgreSQL DB, Vector storage (pgvector), and Edge Functions.
- **AWS SQS**: Message queue for decoupled request processing and enrichment jobs.
- **Gemini**: Embeddings and Chat model for classification, summarization, and matching.
- **Tavily**: Web search optimized for LLM agents.

## Implementation Details

### Cost Controls
The engine enforces several guardrails:
- `MAX_LLM_CALLS_PER_REQUEST`: 5
- `MAX_TAVILY_CALLS_PER_REQUEST`: 10
- `MAX_ARTICLES_PER_CRAWL_RUN`: 20
- `MAX_LLM_CALLS_PER_CRAWL_RUN`: 25

### Monitoring
- `GET /health`: Basic liveness check.
- `GET /status`: Detailed operational metrics including scheduler status, crawler last run times, and matching hit rate.

## Setup

1.  **Clone the repository**
2.  **Install dependencies**:
    ```bash
    uv sync
    ```
3.  **Configure Environment Variables**:
    Create a `.env` file with:
    - `SUPABASE_URL`
    - `SUPABASE_KEY` (Service Role)
    - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
    - `SQS_REQUESTS_QUEUE_URL`
    - `GEMINI_API_KEY`
    - `TAVILY_API_KEY`

4.  **Seed Search Strategies**:
    ```bash
    python -m scripts.seed_strategy
    ```

5.  **Run the application**:
    ```bash
    uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
    ```
