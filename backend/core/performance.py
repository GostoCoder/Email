"""
Performance Optimization Utilities

Provides:
- Pagination helpers
- Bulk insert operations
- Redis caching layer
- Query optimization utilities
- Connection pooling
"""

import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, TypeVar, Generic, Callable
from dataclasses import dataclass
from functools import wraps
import asyncio

from pydantic import BaseModel

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

T = TypeVar('T')


# ==========================================
# Pagination
# ==========================================

@dataclass
class PaginationParams:
    """Pagination parameters"""
    page: int = 1
    page_size: int = 50
    max_page_size: int = 100
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.effective_page_size
    
    @property
    def effective_page_size(self) -> int:
        return min(self.page_size, self.max_page_size)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(
        cls,
        items: List[Any],
        total: int,
        params: PaginationParams
    ) -> "PaginatedResponse":
        page_size = params.effective_page_size
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_prev=params.page > 1,
        )


def paginate_query(query, params: PaginationParams):
    """
    Apply pagination to a Supabase query.
    
    Usage:
        query = supabase.table("recipients").select("*")
        query = paginate_query(query, PaginationParams(page=2, page_size=50))
    """
    return query.range(
        params.offset,
        params.offset + params.effective_page_size - 1
    )


async def get_paginated_results(
    table: str,
    params: PaginationParams,
    filters: Optional[Dict[str, Any]] = None,
    order_by: str = "created_at",
    order_desc: bool = True,
    select: str = "*"
) -> PaginatedResponse:
    """
    Get paginated results from a table.
    """
    from core.supabase import get_supabase_client
    
    supabase = get_supabase_client()
    
    # Build query
    query = supabase.table(table).select(select, count="exact")
    
    # Apply filters
    if filters:
        for key, value in filters.items():
            if isinstance(value, list):
                query = query.in_(key, value)
            else:
                query = query.eq(key, value)
    
    # Apply ordering
    query = query.order(order_by, desc=order_desc)
    
    # Apply pagination
    query = paginate_query(query, params)
    
    # Execute
    result = query.execute()
    
    total = result.count if result.count is not None else len(result.data or [])
    
    return PaginatedResponse.create(
        items=result.data or [],
        total=total,
        params=params
    )


# ==========================================
# Bulk Operations
# ==========================================

async def bulk_insert(
    table: str,
    records: List[Dict[str, Any]],
    batch_size: int = 500,
    on_conflict: Optional[str] = None
) -> Dict[str, int]:
    """
    Bulk insert records in batches.
    
    Args:
        table: Table name
        records: List of records to insert
        batch_size: Number of records per batch
        on_conflict: Column for upsert (optional)
    
    Returns:
        Dict with inserted and failed counts
    """
    from core.supabase import get_supabase_client
    
    supabase = get_supabase_client()
    
    result = {
        "total": len(records),
        "inserted": 0,
        "failed": 0,
        "batches": 0,
    }
    
    # Process in batches
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        
        try:
            if on_conflict:
                # Upsert
                supabase.table(table).upsert(
                    batch,
                    on_conflict=on_conflict
                ).execute()
            else:
                # Insert
                supabase.table(table).insert(batch).execute()
            
            result["inserted"] += len(batch)
            result["batches"] += 1
            
        except Exception as e:
            logger.error(f"Bulk insert batch {i // batch_size} failed: {e}")
            result["failed"] += len(batch)
    
    logger.info(
        f"Bulk insert to {table}: {result['inserted']} inserted, "
        f"{result['failed']} failed in {result['batches']} batches"
    )
    
    return result


async def bulk_update(
    table: str,
    updates: List[Dict[str, Any]],
    id_field: str = "id",
    batch_size: int = 100
) -> Dict[str, int]:
    """
    Bulk update records.
    Each update dict must contain the id_field.
    """
    from core.supabase import get_supabase_client
    
    supabase = get_supabase_client()
    
    result = {
        "total": len(updates),
        "updated": 0,
        "failed": 0,
    }
    
    for update in updates:
        record_id = update.pop(id_field, None)
        if not record_id:
            result["failed"] += 1
            continue
        
        try:
            supabase.table(table).update(update).eq(id_field, record_id).execute()
            result["updated"] += 1
        except Exception as e:
            logger.error(f"Bulk update failed for {record_id}: {e}")
            result["failed"] += 1
    
    return result


async def bulk_delete(
    table: str,
    ids: List[str],
    id_field: str = "id",
    batch_size: int = 500
) -> int:
    """
    Bulk delete records by ID.
    """
    from core.supabase import get_supabase_client
    
    supabase = get_supabase_client()
    deleted = 0
    
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i + batch_size]
        
        try:
            result = supabase.table(table).delete().in_(id_field, batch).execute()
            deleted += len(result.data or [])
        except Exception as e:
            logger.error(f"Bulk delete batch failed: {e}")
    
    return deleted


# ==========================================
# Redis Caching
# ==========================================

class CacheManager:
    """
    Redis-based caching with fallback to in-memory.
    """
    
    def __init__(self):
        self._redis = None
        self._local_cache: Dict[str, tuple] = {}  # key: (value, expires_at)
        self._initialized = False
    
    async def _ensure_connected(self):
        """Ensure Redis connection is established"""
        if self._initialized:
            return
        
        if settings.redis_url:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(settings.redis_url)
                await self._redis.ping()
                logger.info("Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis unavailable, using local cache: {e}")
                self._redis = None
        
        self._initialized = True
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        await self._ensure_connected()
        
        if self._redis:
            try:
                value = await self._redis.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        
        # Fallback to local cache
        if key in self._local_cache:
            value, expires_at = self._local_cache[key]
            if expires_at > datetime.utcnow():
                return value
            else:
                del self._local_cache[key]
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 300
    ):
        """Set value in cache"""
        await self._ensure_connected()
        
        if self._redis:
            try:
                await self._redis.setex(
                    key,
                    ttl_seconds,
                    json.dumps(value, default=str)
                )
                return
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
        
        # Fallback to local cache
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self._local_cache[key] = (value, expires_at)
        
        # Cleanup old entries
        if len(self._local_cache) > 10000:
            self._cleanup_local_cache()
    
    async def delete(self, key: str):
        """Delete value from cache"""
        await self._ensure_connected()
        
        if self._redis:
            try:
                await self._redis.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")
        
        self._local_cache.pop(key, None)
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        await self._ensure_connected()
        
        if self._redis:
            try:
                keys = []
                async for key in self._redis.scan_iter(match=pattern):
                    keys.append(key)
                if keys:
                    await self._redis.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis delete pattern failed: {e}")
        
        # Local cache cleanup
        keys_to_delete = [
            k for k in self._local_cache
            if self._matches_pattern(k, pattern)
        ]
        for k in keys_to_delete:
            del self._local_cache[k]
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches Redis-style pattern"""
        import fnmatch
        return fnmatch.fnmatch(key, pattern.replace("*", "*"))
    
    def _cleanup_local_cache(self):
        """Remove expired entries from local cache"""
        now = datetime.utcnow()
        expired = [
            k for k, (_, exp) in self._local_cache.items()
            if exp < now
        ]
        for k in expired:
            del self._local_cache[k]


# Singleton cache instance
_cache: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """Get or create cache instance"""
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache


def cached(
    key_prefix: str,
    ttl_seconds: int = 300,
    key_builder: Optional[Callable] = None
):
    """
    Decorator for caching function results.
    
    Usage:
        @cached("campaign", ttl_seconds=600)
        async def get_campaign(campaign_id: str) -> dict:
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key builder
                key_parts = [key_prefix]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(key_pattern: str):
    """
    Decorator to invalidate cache after function execution.
    
    Usage:
        @invalidate_cache("campaign:*")
        async def update_campaign(campaign_id: str, data: dict):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            cache = get_cache()
            await cache.delete_pattern(key_pattern)
            
            return result
        
        return wrapper
    return decorator


# ==========================================
# Query Optimization
# ==========================================

def build_efficient_query(
    base_query,
    select_fields: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    order_by: Optional[str] = None,
    order_desc: bool = True,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
):
    """
    Build an optimized query with all common operations.
    """
    query = base_query
    
    # Select specific fields to reduce data transfer
    if select_fields:
        query = query.select(",".join(select_fields))
    
    # Apply filters
    if filters:
        for key, value in filters.items():
            if value is None:
                continue
            if isinstance(value, list):
                query = query.in_(key, value)
            elif isinstance(value, tuple) and len(value) == 2:
                # Range filter: (min, max)
                min_val, max_val = value
                if min_val is not None:
                    query = query.gte(key, min_val)
                if max_val is not None:
                    query = query.lte(key, max_val)
            else:
                query = query.eq(key, value)
    
    # Apply ordering
    if order_by:
        query = query.order(order_by, desc=order_desc)
    
    # Apply pagination
    if limit is not None:
        if offset is not None:
            query = query.range(offset, offset + limit - 1)
        else:
            query = query.limit(limit)
    
    return query


# ==========================================
# Connection Pool Management
# ==========================================

class ConnectionPool:
    """
    Manage database/service connections with pooling.
    """
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self._connections: List[Any] = []
        self._available: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._lock = asyncio.Lock()
        self._created = 0
    
    async def acquire(self) -> Any:
        """Get a connection from the pool"""
        try:
            # Try to get an available connection
            return self._available.get_nowait()
        except asyncio.QueueEmpty:
            pass
        
        # Create new connection if under limit
        async with self._lock:
            if self._created < self.max_size:
                conn = await self._create_connection()
                self._created += 1
                self._connections.append(conn)
                return conn
        
        # Wait for available connection
        return await self._available.get()
    
    async def release(self, conn: Any):
        """Return a connection to the pool"""
        await self._available.put(conn)
    
    async def _create_connection(self) -> Any:
        """Create a new connection (override in subclass)"""
        raise NotImplementedError
    
    async def close_all(self):
        """Close all connections"""
        for conn in self._connections:
            await self._close_connection(conn)
        self._connections.clear()
        self._created = 0
    
    async def _close_connection(self, conn: Any):
        """Close a connection (override in subclass)"""
        pass


# ==========================================
# Batch Processing Utilities
# ==========================================

async def process_in_batches(
    items: List[Any],
    batch_processor: Callable,
    batch_size: int = 100,
    max_concurrent: int = 5
) -> List[Any]:
    """
    Process items in batches with concurrency control.
    
    Args:
        items: List of items to process
        batch_processor: Async function that processes a batch
        batch_size: Items per batch
        max_concurrent: Max concurrent batch operations
    
    Returns:
        List of results from all batches
    """
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(batch: List[Any]) -> Any:
        async with semaphore:
            return await batch_processor(batch)
    
    # Create batches
    batches = [
        items[i:i + batch_size]
        for i in range(0, len(items), batch_size)
    ]
    
    # Process concurrently
    tasks = [process_batch(batch) for batch in batches]
    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Collect results
    for result in batch_results:
        if isinstance(result, Exception):
            logger.error(f"Batch processing error: {result}")
        elif isinstance(result, list):
            results.extend(result)
        else:
            results.append(result)
    
    return results
