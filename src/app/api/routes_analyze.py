from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, Request

from app.core.config import get_settings
from app.core.errors import AppError
from app.demo.scenarios import list_demo_scenarios
from app.services.agent_profiles import list_agent_profiles
from app.services.analyze_ticket import analyze_demo_ticket, analyze_ticket_manual
from app.services.demo_report import build_demo_report_payload

router = APIRouter()


@router.post("/webhook/jira")
async def analyze_from_webhook(
    request: Request,
    dry_run: bool = Query(default=True),
    x_webhook_token: str | None = Header(default=None),
) -> dict:
    settings = get_settings()
    if settings.webhook_token and x_webhook_token != settings.webhook_token:
        raise HTTPException(status_code=401, detail={"message": "Invalid webhook token"})

    payload = await request.json()
    jira_key = _extract_jira_key(payload)
    if not jira_key:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unable to extract Jira issue key from webhook payload",
                "details": {
                    "supported_paths": [
                        "issue.key",
                        "issueKey",
                        "jira_key",
                        "ticket.key",
                    ]
                },
            },
        )

    try:
        return {
            "status": "ok",
            "source": "jira_webhook",
            "jira_key": jira_key,
            "dry_run": dry_run,
            "result": analyze_ticket_manual(jira_key, dry_run=dry_run),
        }
    except AppError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "details": exc.details},
        ) from exc


@router.get("/demo")
def demo_scenarios() -> dict:
    return {"status": "ok", "scenarios": list_demo_scenarios()}


@router.post("/demo/{scenario_id}")
def analyze_demo(scenario_id: str) -> dict:
    try:
        return {"status": "ok", "result": analyze_demo_ticket(scenario_id)}
    except AppError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "details": exc.details},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc


@router.get("/demo/{scenario_id}/report")
def analyze_demo_report(scenario_id: str) -> dict:
    try:
        result = analyze_demo_ticket(scenario_id)
        return {"status": "ok", "report": build_demo_report_payload(result)}
    except AppError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "details": exc.details},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc


@router.post("/{jira_key}")
def analyze(jira_key: str, dry_run: bool = Query(default=True)) -> dict:
    try:
        return {"status": "ok", "result": analyze_ticket_manual(jira_key, dry_run=dry_run)}
    except AppError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "details": exc.details},
        ) from exc


@router.get("/profiles")
def profiles() -> dict:
    return {"status": "ok", "profiles": list_agent_profiles()}


def _extract_jira_key(payload: dict[str, Any]) -> str | None:
    candidates = [
        payload.get("issueKey"),
        payload.get("jira_key"),
        (payload.get("issue") or {}).get("key"),
        (payload.get("jira") or {}).get("issue", {}).get("key"),
        (payload.get("ticket") or {}).get("key"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None
