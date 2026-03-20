from __future__ import annotations

from app.core.config import get_settings
from app.db.session import SessionLocal, init_db
from app.jira.client import JiraClient
from app.storage.tickets import upsert_ticket_from_jira


def sync_recent_tickets_job() -> dict:
    init_db()
    settings = get_settings()
    jira = JiraClient(
        base_url=settings.jira_base_url,
        email=settings.jira_email,
        api_token=settings.jira_api_token,
    )
    jql = (
        f"project = {settings.jira_project_key} "
        f"AND updated >= -{settings.jira_lookback_minutes}m ORDER BY updated DESC"
    )
    payload = jira.search_issues(
        jql=jql,
        fields=[
            "project",
            "summary",
            "description",
            "status",
            "updated",
            "created",
            "assignee",
            "reporter",
            "priority",
            "issuetype",
            "labels",
        ],
        max_results=50,
    )
    issues = payload.get("issues", [])
    session = SessionLocal()
    try:
        synced_keys: list[str] = []
        for issue in issues:
            comments_payload = jira.get_comments(issue["key"])
            upsert_ticket_from_jira(session, issue, comments_payload)
            synced_keys.append(issue["key"])
        session.commit()
        return {"jql": jql, "count": len(synced_keys), "issue_keys": synced_keys}
    finally:
        session.close()
