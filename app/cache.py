import json
import os

try:
    import redis
    _HAS_REDIS = True
except ImportError:
    _HAS_REDIS = False

_client = None


def get_redis():
    global _client
    if not _HAS_REDIS:
        return None
    if _client is None:
        _client = redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", 6379)),
            decode_responses=True,
        )
    return _client


def cache_get(key):
    try:
        r = get_redis()
        if r is None:
            return None
        val = r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


def cache_set(key, data, ttl=60):
    try:
        r = get_redis()
        if r is None:
            return
        r.setex(key, ttl, json.dumps(data, default=str))
    except Exception:
        pass


def cache_delete_pattern(pattern):
    try:
        r = get_redis()
        if r is None:
            return
        for key in r.scan_iter(pattern):
            r.delete(key)
    except Exception:
        pass
