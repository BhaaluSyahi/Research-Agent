"""
One-time script to seed the search_strategy table with default topic configurations.
"""

import asyncio
from supabase import acreate_client, AsyncClient

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

STRATEGIES = [
    {
        "topic": "floods",
        "display_name": "Flood Relief",
        "search_queries": [
            {"query": "NGO flood relief India", "weight": 1.0},
            {"query": "community flood rescue India", "weight": 0.8}
        ],
        "crawl_frequency_hours": 6
    },
    {
        "topic": "drought",
        "display_name": "Drought Response",
        "search_queries": [
            {"query": "drought relief NGO India", "weight": 1.0},
            {"query": "water scarcity village India", "weight": 0.8}
        ],
        "crawl_frequency_hours": 12
    },
    {
        "topic": "healthcare",
        "display_name": "Rural Healthcare",
        "search_queries": [
            {"query": "mobile health NGO rural India", "weight": 1.0}
        ],
        "crawl_frequency_hours": 24
    },
    {
        "topic": "disaster",
        "display_name": "Disaster Relief",
        "search_queries": [
            {"query": "disaster response NGO India", "weight": 1.0}
        ],
        "crawl_frequency_hours": 6
    },
    {
        "topic": "welfare",
        "display_name": "Social Welfare",
        "search_queries": [
            {"query": "community welfare NGO India", "weight": 1.0}
        ],
        "crawl_frequency_hours": 24
    },
    {
        "topic": "education",
        "display_name": "Education Access",
        "search_queries": [
            {"query": "education NGO tribal India", "weight": 1.0}
        ],
        "crawl_frequency_hours": 48
    },
    {
        "topic": "livelihood",
        "display_name": "Livelihood Support",
        "search_queries": [
            {"query": "livelihood NGO farmer India", "weight": 1.0}
        ],
        "crawl_frequency_hours": 48
    },
    {
        "topic": "environment",
        "display_name": "Environment",
        "search_queries": [
            {"query": "environment conservation NGO India", "weight": 1.0}
        ],
        "crawl_frequency_hours": 48
    },
    {
        "topic": "regional_south",
        "display_name": "South India",
        "search_queries": [
            {"query": "NGO volunteer help Kerala Karnataka Tamil Nadu", "weight": 1.0}
        ],
        "crawl_frequency_hours": 12
    },
    {
        "topic": "regional_northeast",
        "display_name": "Northeast India",
        "search_queries": [
            {"query": "NGO volunteer help Assam Meghalaya Manipur", "weight": 1.0}
        ],
        "crawl_frequency_hours": 12
    }
]

async def seed():
    client: AsyncClient = await acreate_client(settings.supabase_url, settings.supabase_key)
    
    logger.info("seeding_strategies_started")
    for strategy in STRATEGIES:
        try:
            # Upsert
            await client.table("search_strategy").upsert(
                strategy,
                on_conflict="topic"
            ).execute()
            logger.info("strategy_seeded", topic=strategy["topic"])
        except Exception as e:
            logger.error("strategy_seed_failed", topic=strategy["topic"], error=str(e))

    logger.info("seeding_strategies_complete")

if __name__ == "__main__":
    asyncio.run(seed())
