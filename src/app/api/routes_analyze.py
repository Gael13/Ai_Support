from fastapi import APIRouter, HTTPException, Query

from app.core.errors import AppError
from app.demo.scenarios import list_demo_scenarios
from app.services.analyze_ticket import analyze_demo_ticket, analyze_ticket_manual

router = APIRouter()


@router.post("/{jira_key}")
def analyze(jira_key: str, dry_run: bool = Query(default=True)) -> dict:
    try:
        return {"status": "ok", "result": analyze_ticket_manual(jira_key, dry_run=dry_run)}
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
