import redis.asyncio as redis
from qdrant_client import AsyncQdrantClient
from sqlalchemy import text

from app.config import settings
from app.db.session import engine


async def check_postgres() -> tuple[bool, str]:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as e:
        return False, str(e)


async def check_redis() -> tuple[bool, str]:
    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        pong = await client.ping()
        return (True, "ok") if pong else (False, "no pong")
    except Exception as e:
        return False, str(e)
    finally:
        await client.aclose()


async def check_qdrant() -> tuple[bool, str]:
    client = AsyncQdrantClient(url=settings.qdrant_url)
    try:
        await client.get_collections()
        return True, "ok"
    except Exception as e:
        return False, str(e)
    finally:
        await client.close()
