"""
Health Check Endpoints

Provides comprehensive health and readiness checks for monitoring.
"""

import asyncio
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])
settings = get_settings()


class HealthStatus(BaseModel):
    """Overall health status response"""
    status: str
    timestamp: str
    version: str
    checks: dict


class ComponentHealth(BaseModel):
    """Individual component health"""
    healthy: bool
    latency_ms: Optional[float] = None
    message: Optional[str] = None


@router.get("", response_model=HealthStatus)
async def healthcheck():
    """
    Comprehensive health check
    
    Returns:
    - status: "healthy", "degraded", or "unhealthy"
    - timestamp: Current server time
    - version: Application version
    - checks: Individual component health statuses
    """
    checks = {}
    overall_healthy = True
    
    # Check Supabase connection
    supabase_health = await check_supabase()
    checks["supabase"] = supabase_health
    if not supabase_health.healthy:
        overall_healthy = False
    
    # Check Redis connection (if configured)
    redis_health = await check_redis()
    checks["redis"] = redis_health
    # Redis is optional - don't fail overall health if it's down
    
    # Check scheduler
    scheduler_health = check_scheduler()
    checks["scheduler"] = scheduler_health
    if not scheduler_health.healthy:
        overall_healthy = False
    
    # Check email provider configuration
    email_health = check_email_config()
    checks["email"] = email_health
    if not email_health.healthy:
        overall_healthy = False
    
    # Determine overall status
    if overall_healthy:
        status = "healthy"
    elif checks["supabase"].healthy and checks["scheduler"].healthy:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return HealthStatus(
        status=status,
        timestamp=datetime.utcnow().isoformat(),
        version="0.1.0",
        checks={k: v.dict() for k, v in checks.items()}
    )


@router.get("/live")
async def liveness():
    """
    Kubernetes liveness probe
    
    Returns 200 if the application is running.
    Fails if the process is deadlocked or unresponsive.
    """
    return {"status": "alive"}


@router.get("/ready")
async def readiness():
    """
    Kubernetes readiness probe
    
    Returns 200 if the application is ready to serve traffic.
    Checks critical dependencies.
    """
    # Check critical dependencies
    supabase_ok = await check_supabase()
    
    if not supabase_ok.healthy:
        raise HTTPException(
            status_code=503,
            detail="Database not ready"
        )
    
    return {"status": "ready"}


# ==========================================
# Component Health Checks
# ==========================================

async def check_supabase() -> ComponentHealth:
    """Check Supabase database connectivity"""
    try:
        from core.supabase import get_supabase_client
        
        start = time.time()
        supabase = get_supabase_client()
        
        # Try a simple query
        result = supabase.table("campaigns").select("id").limit(1).execute()
        
        latency = (time.time() - start) * 1000
        
        return ComponentHealth(
            healthy=True,
            latency_ms=round(latency, 2),
            message="Connected"
        )
    
    except Exception as e:
        return ComponentHealth(
            healthy=False,
            message=f"Connection failed: {str(e)}"
        )


async def check_redis() -> ComponentHealth:
    """Check Redis connectivity (optional)"""
    try:
        import redis.asyncio as redis
        
        if not settings.redis_url:
            return ComponentHealth(
                healthy=True,
                message="Not configured (optional)"
            )
        
        start = time.time()
        
        # Try to connect
        r = redis.from_url(settings.redis_url, decode_responses=True)
        await r.ping()
        await r.close()
        
        latency = (time.time() - start) * 1000
        
        return ComponentHealth(
            healthy=True,
            latency_ms=round(latency, 2),
            message="Connected"
        )
    
    except Exception as e:
        return ComponentHealth(
            healthy=False,
            message=f"Connection failed: {str(e)}"
        )


def check_scheduler() -> ComponentHealth:
    """Check if APScheduler is running"""
    try:
        from core.scheduler import get_scheduler
        
        scheduler = get_scheduler()
        
        if scheduler.running:
            job_count = len(scheduler.get_jobs())
            return ComponentHealth(
                healthy=True,
                message=f"Running with {job_count} jobs"
            )
        else:
            return ComponentHealth(
                healthy=False,
                message="Scheduler not running"
            )
    
    except Exception as e:
        return ComponentHealth(
            healthy=False,
            message=f"Scheduler error: {str(e)}"
        )


def check_email_config() -> ComponentHealth:
    """Check if email provider is configured"""
    try:
        provider = settings.email_provider
        
        if not provider or provider == "smtp":
            # Check SMTP config
            if not settings.smtp_host:
                return ComponentHealth(
                    healthy=False,
                    message="No email provider configured"
                )
        
        return ComponentHealth(
            healthy=True,
            message=f"Using {provider or 'smtp'}"
        )
    
    except Exception as e:
        return ComponentHealth(
            healthy=False,
            message=f"Config error: {str(e)}"
        )

