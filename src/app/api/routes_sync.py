from fastapi import APIRouter, HTTPException, Query

from app.core.errors import AppError
from app.core.config import get_settings
from app.jira.client import JiraClient
from app.workers.sync_recent import sync_recent_tickets_job

router = APIRouter()


@router.post("")
def sync_now() -> dict:
    return {"status": "ok", "result": sync_recent_tickets_job()}


@router.get("/recent")
def list_recent_tickets(
    max_results: int = Query(default=10, ge=1, le=50),
    project_key: str | None = Query(default=None),
) -> dict:
    settings = get_settings()
    jira = JiraClient(
        base_url=settings.jira_base_url,
        email=settings.jira_email,
        api_token=settings.jira_api_token,
    )
    project = project_key or settings.jira_project_key
    jql = f"project = {project} ORDER BY created DESC"
    try:
        payload = jira.search_issues(
            jql=jql,
            fields=["summary", "created", "status", "description"],
            max_results=max_results,
        )
    except AppError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "details": exc.details},
        ) from exc

    issues = payload.get("issues", [])
    return {
        "project_key": project,
        "count": len(issues),
        "issues": [
            {
                "id": issue.get("id"),
                "key": issue.get("key"),
                "summary": (issue.get("fields") or {}).get("summary"),
                "created": (issue.get("fields") or {}).get("created"),
                "status": ((issue.get("fields") or {}).get("status") or {}).get("name"),
            }
            for issue in issues
        ],
    }
