"""
Observability Module

Provides:
- OpenTelemetry tracing integration
- Prometheus metrics
- Structured JSON logging
- Request/Response logging
- Performance monitoring
"""

import time
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from contextvars import ContextVar
from functools import wraps
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import get_settings

settings = get_settings()


# ==========================================
# Structured Logging
# ==========================================

class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Compatible with ELK, Loki, CloudWatch, etc.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Add common fields from context
        request_id = request_id_context.get(None)
        if request_id:
            log_data["request_id"] = request_id
        
        return json.dumps(log_data)


class ContextualLogger(logging.LoggerAdapter):
    """Logger adapter that adds contextual information"""
    
    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        
        # Add request ID from context
        request_id = request_id_context.get(None)
        if request_id:
            extra["request_id"] = request_id
        
        kwargs["extra"] = extra
        return msg, kwargs


# Context variable for request ID
request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def setup_logging(log_level: str | int = "INFO", json_format: bool = True):
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR) or int
        json_format: If True, use JSON formatting
    """
    root_logger = logging.getLogger()
    if isinstance(log_level, str):
        root_logger.setLevel(getattr(logging, log_level.upper()))
    else:
        root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
    
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> ContextualLogger:
    """Get a contextual logger"""
    return ContextualLogger(logging.getLogger(name), {})


# ==========================================
# Prometheus Metrics
# ==========================================

class PrometheusMetrics:
    """
    Simple Prometheus metrics collector.
    For production, consider using prometheus_client library.
    """
    
    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = {}
        self._labels: Dict[str, Dict[str, Any]] = {}
    
    def inc_counter(self, name: str, value: int = 1, labels: Optional[Dict] = None):
        """Increment a counter"""
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value
        self._labels[key] = labels or {}
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict] = None):
        """Set a gauge value"""
        key = self._make_key(name, labels)
        self._gauges[key] = value
        self._labels[key] = labels or {}
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict] = None):
        """Observe a histogram value"""
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        self._labels[key] = labels or {}
        
        # Keep only last 1000 observations
        if len(self._histograms[key]) > 1000:
            self._histograms[key] = self._histograms[key][-1000:]
    
    def _make_key(self, name: str, labels: Optional[Dict]) -> str:
        """Create a unique key for metric with labels"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Export counters
        for key, value in self._counters.items():
            lines.append(f"{key} {value}")
        
        # Export gauges
        for key, value in self._gauges.items():
            lines.append(f"{key} {value}")
        
        # Export histograms (simplified)
        for key, values in self._histograms.items():
            if values:
                count = len(values)
                total = sum(values)
                lines.append(f"{key}_count {count}")
                lines.append(f"{key}_sum {total}")
        
        return "\n".join(lines)
    
    def get_metrics_json(self) -> Dict[str, Any]:
        """Export metrics as JSON"""
        result = {
            "counters": {},
            "gauges": {},
            "histograms": {},
        }
        
        for key, value in self._counters.items():
            result["counters"][key] = value
        
        for key, value in self._gauges.items():
            result["gauges"][key] = value
        
        for key, values in self._histograms.items():
            if values:
                result["histograms"][key] = {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }
        
        return result


# Singleton metrics instance
_metrics: Optional[PrometheusMetrics] = None


def get_metrics() -> PrometheusMetrics:
    """Get or create metrics instance"""
    global _metrics
    if _metrics is None:
        _metrics = PrometheusMetrics()
    return _metrics


# Pre-defined metrics
class EmailMetrics:
    """Email-specific metrics"""
    
    @staticmethod
    def record_email_sent(campaign_id: str, provider: str):
        metrics = get_metrics()
        metrics.inc_counter("emails_sent_total", labels={
            "campaign_id": campaign_id,
            "provider": provider,
        })
    
    @staticmethod
    def record_email_failed(campaign_id: str, provider: str, reason: str):
        metrics = get_metrics()
        metrics.inc_counter("emails_failed_total", labels={
            "campaign_id": campaign_id,
            "provider": provider,
            "reason": reason[:20],
        })
    
    @staticmethod
    def record_email_opened(campaign_id: str):
        metrics = get_metrics()
        metrics.inc_counter("emails_opened_total", labels={
            "campaign_id": campaign_id,
        })
    
    @staticmethod
    def record_email_clicked(campaign_id: str):
        metrics = get_metrics()
        metrics.inc_counter("emails_clicked_total", labels={
            "campaign_id": campaign_id,
        })
    
    @staticmethod
    def record_send_latency(campaign_id: str, latency_ms: float):
        metrics = get_metrics()
        metrics.observe_histogram("email_send_latency_ms", latency_ms, labels={
            "campaign_id": campaign_id,
        })


# ==========================================
# Request/Response Middleware
# ==========================================

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response observability.
    Adds request ID, timing, and logging.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4())[:8])
        request_id_context.set(request_id)
        
        # Start timing
        start_time = time.time()
        
        # Get request info
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        logger = get_logger("http")
        logger.info(
            f"Request started: {method} {path}",
            extra={
                "method": method,
                "path": path,
                "client_ip": client_ip,
                "query_params": str(request.query_params),
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            metrics = get_metrics()
            metrics.inc_counter("http_requests_total", labels={
                "method": method,
                "path": self._normalize_path(path),
                "status": str(response.status_code),
            })
            metrics.observe_histogram("http_request_duration_ms", duration_ms, labels={
                "method": method,
                "path": self._normalize_path(path),
            })
            
            # Log response
            logger.info(
                f"Request completed: {method} {path} - {response.status_code}",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            )
            
            # Add headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Record error metrics
            metrics = get_metrics()
            metrics.inc_counter("http_requests_total", labels={
                "method": method,
                "path": self._normalize_path(path),
                "status": "500",
            })
            
            # Log error
            logger.error(
                f"Request failed: {method} {path}",
                extra={
                    "method": method,
                    "path": path,
                    "error": str(e),
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=True
            )
            
            raise
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for metrics (replace UUIDs, IDs)"""
        import re
        # Replace UUIDs
        path = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            ':id',
            path
        )
        # Replace numeric IDs
        path = re.sub(r'/\d+(?=/|$)', '/:id', path)
        return path


# ==========================================
# OpenTelemetry Tracing (Simplified)
# ==========================================

class SimpleTracer:
    """
    Simple tracing implementation.
    For production, use OpenTelemetry SDK.
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._spans: Dict[str, Dict] = {}
    
    def start_span(
        self,
        name: str,
        parent_id: Optional[str] = None,
        attributes: Optional[Dict] = None
    ) -> str:
        """Start a new span"""
        span_id = str(uuid4())[:16]
        trace_id = parent_id[:32] if parent_id else str(uuid4())[:32]
        
        self._spans[span_id] = {
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_id": parent_id,
            "name": name,
            "service": self.service_name,
            "start_time": time.time(),
            "end_time": None,
            "attributes": attributes or {},
            "status": "OK",
        }
        
        return span_id
    
    def end_span(self, span_id: str, status: str = "OK", error: Optional[str] = None):
        """End a span"""
        if span_id in self._spans:
            span = self._spans[span_id]
            span["end_time"] = time.time()
            span["status"] = status
            if error:
                span["error"] = error
            
            # Log completed span
            duration = (span["end_time"] - span["start_time"]) * 1000
            logger = get_logger("tracing")
            logger.debug(
                f"Span completed: {span['name']}",
                extra={
                    "trace_id": span["trace_id"],
                    "span_id": span_id,
                    "duration_ms": round(duration, 2),
                    "status": status,
                }
            )
            
            # Clean up old spans
            if len(self._spans) > 1000:
                oldest = sorted(
                    self._spans.items(),
                    key=lambda x: x[1]["start_time"]
                )[:500]
                for sid, _ in oldest:
                    del self._spans[sid]
    
    def add_attribute(self, span_id: str, key: str, value: Any):
        """Add attribute to a span"""
        if span_id in self._spans:
            self._spans[span_id]["attributes"][key] = value


# Singleton tracer instance
_tracer: Optional[SimpleTracer] = None


def get_tracer() -> SimpleTracer:
    """Get or create tracer instance"""
    global _tracer
    if _tracer is None:
        _tracer = SimpleTracer(settings.app_name)
    return _tracer


def trace(name: Optional[str] = None):
    """
    Decorator for tracing function execution.
    
    Usage:
        @trace("send_email")
        async def send_email(to: str, subject: str):
            ...
    """
    def decorator(func: Callable):
        span_name = name or func.__name__
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_id = tracer.start_span(span_name)
            
            try:
                result = await func(*args, **kwargs)
                tracer.end_span(span_id, status="OK")
                return result
            except Exception as e:
                tracer.end_span(span_id, status="ERROR", error=str(e))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_id = tracer.start_span(span_name)
            
            try:
                result = func(*args, **kwargs)
                tracer.end_span(span_id, status="OK")
                return result
            except Exception as e:
                tracer.end_span(span_id, status="ERROR", error=str(e))
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ==========================================
# Health & Readiness Probes
# ==========================================

async def check_health() -> Dict[str, Any]:
    """
    Comprehensive health check.
    Returns status of all dependencies.
    """
    from core.supabase import get_supabase_client
    
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }
    
    # Check Supabase
    try:
        supabase = get_supabase_client()
        supabase.table("campaigns").select("id").limit(1).execute()
        health["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "unhealthy"
    
    # Check Redis (if configured)
    if settings.redis_url:
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            r.ping()
            health["checks"]["redis"] = {"status": "healthy"}
        except Exception as e:
            health["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
            health["status"] = "degraded"
    
    # Add metrics
    metrics = get_metrics()
    health["metrics"] = metrics.get_metrics_json()
    
    return health
