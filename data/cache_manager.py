"""diskcache 기반 캐싱 계층"""

import os
import diskcache

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
_cache = diskcache.Cache(CACHE_DIR)


def get_or_fetch(key: str, fetch_fn, ttl: int = 900):
    """캐시에서 가져오거나, 없으면 fetch_fn 실행 후 저장"""
    result = _cache.get(key)
    if result is not None:
        return result
    result = fetch_fn()
    # 빈 리스트/None은 캐시하지 않음 (실패한 결과 방지)
    # DataFrame은 직접 비교 불가 → isinstance 체크
    if result is None:
        return result
    if isinstance(result, list) and len(result) == 0:
        return result
    if isinstance(result, dict) and len(result) == 0:
        return result
    _cache.set(key, result, expire=ttl)
    return result


def invalidate(key: str):
    _cache.delete(key)


def clear_all():
    _cache.clear()
