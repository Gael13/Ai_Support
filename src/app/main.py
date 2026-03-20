from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes_analyze import router as analyze_router
from app.api.routes_health import router as health_router
from app.api.routes_sync import router as sync_router
from app.core.config import get_settings
from app.workers.scheduler import build_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    scheduler = None
    if settings.enable_scheduler:
        scheduler = build_scheduler(settings.jira_poll_interval_seconds)
        scheduler.start()
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


app = FastAPI(title="AI Support POC", lifespan=lifespan)
app.include_router(health_router)
app.include_router(sync_router, prefix="/sync", tags=["sync"])
app.include_router(analyze_router, prefix="/analyze", tags=["analyze"])
