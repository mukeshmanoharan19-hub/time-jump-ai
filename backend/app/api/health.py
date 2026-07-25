from fastapi import APIRouter

from app.services.health import check_postgres, check_qdrant, check_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    postgres_ok, postgres_msg = await check_postgres()
    redis_ok, redis_msg = await check_redis()
    qdrant_ok, qdrant_msg = await check_qdrant()

    all_ok = postgres_ok and redis_ok and qdrant_ok
    return {
        "status": "healthy" if all_ok else "degraded",
        "services": {
            "postgres": {"ok": postgres_ok, "detail": postgres_msg},
            "redis": {"ok": redis_ok, "detail": redis_msg},
            "qdrant": {"ok": qdrant_ok, "detail": qdrant_msg},
        },
    }
