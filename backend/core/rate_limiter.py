"""
Rate Limiting & Anti-Abuse Protection Module

Provides:
- IP-based rate limiting
- User-based rate limiting  
- Endpoint-specific limits
- Distributed rate limiting with Redis
- Abuse detection and blocking
"""

import time
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from collections import defaultdict
from functools import wraps

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    """Raised when rate limit is exceeded"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )


class InMemoryRateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.
    For production, use RedisRateLimiter instead.
    """
    
    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
        self._blocked_ips: Dict[str, datetime] = {}
        self._abuse_scores: Dict[str, int] = defaultdict(int)
    
    def _cleanup_old_requests(self, key: str, window_seconds: int):
        """Remove requests outside the time window"""
        cutoff = time.time() - window_seconds
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]
    
    def is_blocked(self, identifier: str) -> bool:
        """Check if an identifier is temporarily blocked"""
        if identifier in self._blocked_ips:
            if datetime.utcnow() < self._blocked_ips[identifier]:
                return True
            del self._blocked_ips[identifier]
        return False
    
    def block(self, identifier: str, duration_seconds: int = 3600):
        """Block an identifier for a specified duration"""
        self._blocked_ips[identifier] = datetime.utcnow() + timedelta(seconds=duration_seconds)
        logger.warning(f"Blocked identifier {identifier} for {duration_seconds}s")
    
    def record_abuse(self, identifier: str, points: int = 1):
        """Record abuse points for an identifier"""
        self._abuse_scores[identifier] += points
        if self._abuse_scores[identifier] >= 10:
            self.block(identifier, duration_seconds=3600)  # 1 hour block
            self._abuse_scores[identifier] = 0
    
    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check if request is allowed under rate limit.
        Returns (allowed, remaining_requests)
        """
        if self.is_blocked(identifier):
            return False, 0
        
        self._cleanup_old_requests(identifier, window_seconds)
        current_count = len(self._requests[identifier])
        
        if current_count >= max_requests:
            self.record_abuse(identifier)
            return False, 0
        
        self._requests[identifier].append(time.time())
        return True, max_requests - current_count - 1
    
    def get_reset_time(self, identifier: str, window_seconds: int) -> int:
        """Get seconds until rate limit resets"""
        if not self._requests[identifier]:
            return 0
        oldest = min(self._requests[identifier])
        reset_time = int(oldest + window_seconds - time.time())
        return max(0, reset_time)


class RedisRateLimiter:
    """
    Redis-based distributed rate limiter using sliding window.
    Falls back to in-memory if Redis is unavailable.
    """
    
    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._fallback = InMemoryRateLimiter()
    
    async def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """Check rate limit using Redis or fallback"""
        if not self._redis:
            return self._fallback.check_rate_limit(identifier, max_requests, window_seconds)
        
        try:
            key = f"ratelimit:{identifier}"
            now = time.time()
            window_start = now - window_seconds
            
            pipe = self._redis.pipeline()
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Count current entries
            pipe.zcard(key)
            # Add current request
            pipe.zadd(key, {str(now): now})
            # Set expiry
            pipe.expire(key, window_seconds)
            
            results = await pipe.execute()
            current_count = results[1]
            
            if current_count >= max_requests:
                return False, 0
            
            return True, max_requests - current_count - 1
            
        except Exception as e:
            logger.warning(f"Redis rate limit error, using fallback: {e}")
            return self._fallback.check_rate_limit(identifier, max_requests, window_seconds)


# Singleton rate limiter instance
_rate_limiter: Optional[InMemoryRateLimiter] = None


def get_rate_limiter() -> InMemoryRateLimiter:
    """Get or create rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = InMemoryRateLimiter()
    return _rate_limiter


# Rate limit configurations per endpoint
RATE_LIMIT_CONFIGS = {
    # Critical endpoints - strict limits
    "/v1/campaigns/{campaign_id}/send": {"max_requests": 5, "window_seconds": 60},
    "/v1/campaigns/{campaign_id}/schedule": {"max_requests": 10, "window_seconds": 60},
    
    # Authentication endpoints - prevent brute force
    "/v1/auth/login": {"max_requests": 5, "window_seconds": 300},
    "/v1/auth/register": {"max_requests": 3, "window_seconds": 3600},
    
    # Import endpoints - resource intensive
    "/v1/campaigns/{campaign_id}/import": {"max_requests": 10, "window_seconds": 300},
    
    # General API endpoints - moderate limits
    "/v1/campaigns": {"max_requests": 100, "window_seconds": 60},
    "/v1/templates": {"max_requests": 100, "window_seconds": 60},
    
    # Tracking endpoints - high volume allowed
    "/v1/track/open": {"max_requests": 1000, "window_seconds": 60},
    "/v1/track/click": {"max_requests": 1000, "window_seconds": 60},
    
    # Default limit
    "default": {"max_requests": 60, "window_seconds": 60},
}


def get_client_identifier(request: Request) -> str:
    """Extract unique client identifier from request"""
    # Try to get real IP behind proxy
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    
    # Include user agent for additional fingerprinting
    user_agent = request.headers.get("User-Agent", "")[:100]
    
    # Create hash for privacy
    identifier = hashlib.sha256(f"{ip}:{user_agent}".encode()).hexdigest()[:16]
    
    return f"{ip}:{identifier}"


def get_rate_limit_config(path: str) -> dict:
    """Get rate limit config for a path, with pattern matching"""
    # Check exact match first
    if path in RATE_LIMIT_CONFIGS:
        return RATE_LIMIT_CONFIGS[path]
    
    # Check pattern matches (replace UUIDs with placeholder)
    import re
    normalized_path = re.sub(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        '{campaign_id}',
        path
    )
    
    if normalized_path in RATE_LIMIT_CONFIGS:
        return RATE_LIMIT_CONFIGS[normalized_path]
    
    # Default config
    return RATE_LIMIT_CONFIGS["default"]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    Apply to entire application or specific routers.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        limiter = get_rate_limiter()
        client_id = get_client_identifier(request)
        config = get_rate_limit_config(request.url.path)
        
        allowed, remaining = limiter.check_rate_limit(
            identifier=f"{client_id}:{request.url.path}",
            max_requests=config["max_requests"],
            window_seconds=config["window_seconds"]
        )
        
        if not allowed:
            reset_time = limiter.get_reset_time(
                f"{client_id}:{request.url.path}",
                config["window_seconds"]
            )
            logger.warning(f"Rate limit exceeded for {client_id} on {request.url.path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": reset_time
                },
                headers={
                    "Retry-After": str(reset_time),
                    "X-RateLimit-Limit": str(config["max_requests"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + reset_time)
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(config["max_requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """
    Decorator for rate limiting specific endpoints.
    
    Usage:
        @router.post("/send")
        @rate_limit(max_requests=5, window_seconds=60)
        async def send_campaign(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request in args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break
            
            if request:
                limiter = get_rate_limiter()
                client_id = get_client_identifier(request)
                
                allowed, _ = limiter.check_rate_limit(
                    identifier=f"{client_id}:{func.__name__}",
                    max_requests=max_requests,
                    window_seconds=window_seconds
                )
                
                if not allowed:
                    raise RateLimitExceeded(retry_after=window_seconds)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Abuse detection patterns
ABUSE_PATTERNS = {
    "sql_injection": [
        "' OR ", "'; DROP", "UNION SELECT", "--", "/*", "*/",
        "1=1", "1'='1", "admin'--"
    ],
    "xss": [
        "<script>", "javascript:", "onerror=", "onload=",
        "<iframe", "<object", "eval("
    ],
    "path_traversal": [
        "../", "..\\", "%2e%2e", "..%c0%af"
    ]
}


def detect_abuse(request: Request) -> Optional[str]:
    """
    Detect potential abuse patterns in requests.
    Returns abuse type if detected, None otherwise.
    """
    # Check URL path
    path = request.url.path.lower()
    query = str(request.url.query).lower()
    
    for abuse_type, patterns in ABUSE_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in path or pattern.lower() in query:
                return abuse_type
    
    return None


class AbuseDetectionMiddleware(BaseHTTPMiddleware):
    """Middleware to detect and block abusive requests"""
    
    async def dispatch(self, request: Request, call_next):
        abuse_type = detect_abuse(request)
        
        if abuse_type:
            limiter = get_rate_limiter()
            client_id = get_client_identifier(request)
            
            # Record abuse and potentially block
            limiter.record_abuse(client_id, points=5)
            
            logger.warning(
                f"Abuse detected: {abuse_type} from {client_id} "
                f"on {request.url.path}"
            )
            
            return JSONResponse(
                status_code=400,
                content={"detail": "Bad request"}
            )
        
        return await call_next(request)
