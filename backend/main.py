import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from core.config import get_settings
from core.scheduler import get_scheduler, shutdown_scheduler

# Feature routers
from features.health.endpoints import router as health_router
from features.apps.endpoints import router as apps_router
from features.campaigns.endpoints import router as campaigns_router
from features.analytics.endpoints import router as analytics_router
from features.abtesting.endpoints import router as abtesting_router
from features.segmentation.endpoints import router as segmentation_router
from features.bounces.endpoints import router as bounces_router

# Security & Observability
from core.rate_limiter import RateLimitMiddleware, AbuseDetectionMiddleware
from core.observability import ObservabilityMiddleware, setup_logging
from core.secrets_manager import validate_secrets_on_startup
from core.security import SecurityHeadersMiddleware

settings = get_settings()

# Setup structured logging
setup_logging(
    log_level=logging.DEBUG if settings.DEBUG else logging.INFO,
    json_format=not settings.DEBUG
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - start scheduler on startup, shutdown on exit"""
    # Startup
    logger.info("Starting application...")
    
    # Validate secrets on startup (warns in dev, fails in prod if critical secrets missing)
    try:
        validate_secrets_on_startup(settings)
    except Exception as e:
        logger.error(f"Secret validation failed: {e}")
        if not settings.DEBUG:
            raise
    
    # Initialize the scheduler
    get_scheduler()
    
    logger.info(f"Application started: {settings.app_name}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    shutdown_scheduler()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ==========================================
# Middleware Stack (order matters - last added = first executed)
# ==========================================

# CORS - must be first to handle preflight requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Observability (logging, metrics, tracing)
app.add_middleware(ObservabilityMiddleware)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# Abuse detection (IP-based patterns)
app.add_middleware(AbuseDetectionMiddleware)

# ==========================================
# Routers
# ==========================================

# Core routers
app.include_router(health_router)
app.include_router(apps_router, prefix="/v1/apps", tags=["apps"])
app.include_router(campaigns_router, prefix="/v1", tags=["campaigns"])

# Analytics & A/B Testing
app.include_router(analytics_router, prefix="/v1", tags=["analytics"])
app.include_router(abtesting_router, prefix="/v1", tags=["abtesting"])

# Segmentation & Suppression
app.include_router(segmentation_router, prefix="/v1", tags=["segmentation"])

# Webhooks (no auth required for provider callbacks)
app.include_router(bounces_router, prefix="/v1", tags=["bounces"])


@app.get("/", response_class=JSONResponse)
async def root():
    return {"service": settings.app_name, "status": "ok"}
