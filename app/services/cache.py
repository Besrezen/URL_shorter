import json
from typing import Any, Optional

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


def set_json(key: str, value: Any, ex: int = 3600) -> None:
    try:
        redis_client.set(key, json.dumps(value, default=str), ex=ex)
    except RedisError:
        # Degrade gracefully when Redis is unavailable.
        return


def get_json(key: str) -> Optional[Any]:
    try:
        data = redis_client.get(key)
    except RedisError:
        return None
    return json.loads(data) if data else None


def delete_pattern(prefix: str) -> None:
    try:
        for key in redis_client.scan_iter(f'{prefix}*'):
            redis_client.delete(key)
    except RedisError:
        return
