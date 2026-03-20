from apscheduler.schedulers.background import BackgroundScheduler

from app.workers.analyze_recent import analyze_recent_tickets_job
from app.workers.sync_recent import sync_recent_tickets_job


def build_scheduler(interval_seconds: int) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        sync_recent_tickets_job,
        trigger="interval",
        seconds=interval_seconds,
        id="sync_recent_tickets",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        analyze_recent_tickets_job,
        trigger="interval",
        seconds=interval_seconds,
        id="analyze_recent_tickets",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler
