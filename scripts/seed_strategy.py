"""
One-time script to seed the search_strategy table.
Run manually: uv run python scripts/seed_strategy.py
Do not run in application code.
"""

import asyncio
import json

from supabase import acreate_client

from app.config import settings

SEED_DATA = [
    {
        "topic": "floods",
        "display_name": "Flood Relief",
        "search_queries": json.dumps([
            {"query": "NGO flood relief India", "weight": 1.0},
            {"query": "community flood rescue India", "weight": 0.8},
        ]),
        "crawl_frequency_hours": 6,
    },
    {
        "topic": "drought",
        "display_name": "Drought Response",
        "search_queries": json.dumps([
            {"query": "drought relief NGO India", "weight": 1.0},
            {"query": "water scarcity village India", "weight": 0.8},
        ]),
        "crawl_frequency_hours": 12,
    },
    {
        "topic": "healthcare",
        "display_name": "Rural Healthcare",
        "search_queries": json.dumps([{"query": "mobile health NGO rural India", "weight": 1.0}]),
        "crawl_frequency_hours": 24,
    },
    {
        "topic": "disaster",
        "display_name": "Disaster Relief",
        "search_queries": json.dumps([{"query": "disaster response NGO India", "weight": 1.0}]),
        "crawl_frequency_hours": 6,
    },
    {
        "topic": "welfare",
        "display_name": "Social Welfare",
        "search_queries": json.dumps([{"query": "community welfare NGO India", "weight": 1.0}]),
        "crawl_frequency_hours": 24,
    },
    {
        "topic": "education",
        "display_name": "Education Access",
        "search_queries": json.dumps([{"query": "education NGO tribal India", "weight": 1.0}]),
        "crawl_frequency_hours": 48,
    },
    {
        "topic": "livelihood",
        "display_name": "Livelihood Support",
        "search_queries": json.dumps([{"query": "livelihood NGO farmer India", "weight": 1.0}]),
        "crawl_frequency_hours": 48,
    },
    {
        "topic": "environment",
        "display_name": "Environment",
        "search_queries": json.dumps([{"query": "environment conservation NGO India", "weight": 1.0}]),
        "crawl_frequency_hours": 48,
    },
    {
        "topic": "regional_south",
        "display_name": "South India",
        "search_queries": json.dumps([{"query": "NGO volunteer help Kerala Karnataka Tamil Nadu", "weight": 1.0}]),
        "crawl_frequency_hours": 12,
    },
    {
        "topic": "regional_northeast",
        "display_name": "Northeast India",
        "search_queries": json.dumps([{"query": "NGO volunteer help Assam Meghalaya Manipur", "weight": 1.0}]),
        "crawl_frequency_hours": 12,
    },
]


async def seed() -> None:
    client = await acreate_client(settings.supabase_url, settings.supabase_key)
    for row in SEED_DATA:
        response = await client.table("search_strategy").upsert(row, on_conflict="topic").execute()
        print(f"Seeded topic: {row['topic']}")
    print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
