import json
import os

import redis

_client = None


def get_redis():
    global _client
    if _client is None:
        _client = redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", 6379)),
            decode_responses=True,
        )
    return _client


def cache_get(key):
    try:
        val = get_redis().get(key)
        return json.loads(val) if val else None
    except redis.ConnectionError:
        return None


def cache_set(key, data, ttl=60):
    try:
        get_redis().setex(key, ttl, json.dumps(data, default=str))
    except redis.ConnectionError:
        pass


def cache_delete_pattern(pattern):
    try:
        r = get_redis()
        for key in r.scan_iter(pattern):
            r.delete(key)
    except redis.ConnectionError:
        pass
