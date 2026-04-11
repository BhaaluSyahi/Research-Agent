# Matching Engine

Standalone Python microservice that intelligently matches help requests with NGOs and volunteers using formal DB queries and informal RAG-based knowledge retrieval.

## Tech Stack

- **Python 3.11+** · **FastAPI** · **uv** (package manager)
- **Supabase** (PostgreSQL + pgvector) · **AWS SQS/SNS** · **LlamaIndex**
- **OpenAI** (gpt-4o + text-embedding-3-small) · **Tavily** · **APScheduler**

## Setup

1. **Install dependencies**
   ```bash
   uv sync
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Run migrations** (Supabase SQL editor — run in order)
   ```
   migrations/001_informal_knowledge_base.sql
   migrations/002_search_strategy.sql
   migrations/003_kpis_and_logs.sql
   migrations/seed_search_strategy.sql
   ```

4. **Start the server**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

5. **Verify**
   ```bash
   curl http://localhost:8000/health
   # {"status":"ok"}
   ```

## Project Structure

See [`antigravity-context/04_CODE_STRUCTURE.md`](antigravity-context/04_CODE_STRUCTURE.md) for the full directory layout.

## Build Phases

| Phase | Goal | Status |
|---|---|---|
| 1 | Scaffold | ✅ Complete |
| 2 | Repositories | 🔲 |
| 3 | MCP Tools + Guardrails | 🔲 |
| 4 | Request Receiver | 🔲 |
| 5 | Formal Matching | 🔲 |
| 6 | Informal Matching (RAG) | 🔲 |
| 7 | On-Demand Enricher | 🔲 |
| 8 | Full Pipeline | 🔲 |
| 9 | Proactive Search Fleet | 🔲 |
| 10 | Hardening | 🔲 |

## Running Tests

```bash
uv run pytest
```
