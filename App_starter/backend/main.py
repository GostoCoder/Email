from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from core.config import get_settings
from features.health.endpoints import router as health_router
from features.apps.endpoints import router as apps_router
from features.campaigns.endpoints import router as campaigns_router

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(apps_router, prefix="/v1/apps", tags=["apps"])
app.include_router(campaigns_router, prefix="/v1", tags=["campaigns"])


@app.get("/", response_class=JSONResponse)
async def root():
    return {"service": settings.app_name, "status": "ok"}
