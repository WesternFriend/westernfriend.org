"""Helpers for tests that run against the production database cache.

Production stores the default cache in PostgreSQL, so each cache read is a
SQL query. These helpers reproduce that configuration and count reads
separately from the cull check and write path inside ``DatabaseCache.set``.
"""

from core.settings import DATABASE_CACHE_TABLE, RENDITION_CACHE_TIMEOUT

DATABASE_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": DATABASE_CACHE_TABLE,
    },
    "renditions": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "renditions",
        "TIMEOUT": RENDITION_CACHE_TIMEOUT,
    },
}


def django_cache_queries(queries) -> int:
    """Count every SQL statement that touches the database cache table."""
    return sum(DATABASE_CACHE_TABLE in query["sql"] for query in queries)


def django_cache_reads(queries) -> int:
    """Count ``django_cache`` reads.

    ``DatabaseCache.get`` selects ``cache_key``, ``value``, and ``expires``.
    ``DatabaseCache.set`` also selects ``COUNT(*)`` and then ``cache_key``
    with ``expires`` before it writes. Those are not reads.
    """
    reads = 0
    for query in queries:
        sql = query["sql"]
        if DATABASE_CACHE_TABLE not in sql:
            continue
        normalized = " ".join(sql.split()).upper()
        if not normalized.startswith("SELECT"):
            continue
        select_list = normalized.split(" FROM ", 1)[0]
        if "COUNT(" in select_list or "VALUE" not in select_list:
            continue
        reads += 1
    return reads
