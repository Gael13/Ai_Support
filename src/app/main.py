from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, Response

from app.api.routes_analyze import router as analyze_router
from app.api.routes_demo_ui import router as demo_ui_router
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


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/demo-ui/", status_code=307)


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


app.include_router(health_router)
app.include_router(demo_ui_router, prefix="/demo-ui", tags=["demo-ui"])
app.include_router(sync_router, prefix="/sync", tags=["sync"])
app.include_router(analyze_router, prefix="/analyze", tags=["analyze"])
