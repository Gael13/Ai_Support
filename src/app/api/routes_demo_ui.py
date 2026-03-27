from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.errors import AppError
from app.demo.scenarios import list_demo_scenarios
from app.services.agent_profiles import list_agent_profiles
from app.services.analyze_ticket import analyze_demo_ticket
from app.services.demo_report import build_demo_report_payload

router = APIRouter()
templates = Jinja2Templates(directory="src/app/templates")


@router.get("/", response_class=HTMLResponse)
def demo_home(request: Request, scenario_id: str | None = None) -> HTMLResponse:
    scenarios = list_demo_scenarios()
    selected = scenario_id or (scenarios[0]["scenario_id"] if scenarios else None)
    report = None
    error = None

    if selected:
        try:
            result = analyze_demo_ticket(selected)
            report = build_demo_report_payload(result)
        except AppError as exc:
            error = {"message": exc.message, "details": exc.details}
        except ValueError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    return templates.TemplateResponse(
        request,
        "demo_home.html",
        {
            "scenarios": scenarios,
            "selected_scenario_id": selected,
            "report": report,
            "error": error,
        },
    )


@router.get("/profiles", response_class=HTMLResponse)
def demo_profiles(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "profiles.html",
        {
            "profiles": list_agent_profiles(),
        },
    )
