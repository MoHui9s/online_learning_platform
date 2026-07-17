"""Redis 连接客户端（依赖 docker-compose 启动的 Redis 容器）。"""
import redis

from app.core.config import settings

_redis_pool: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """获取 Redis 单例连接。"""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,
        )
    return _redis_pool
