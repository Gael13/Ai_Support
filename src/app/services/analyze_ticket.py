from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.db.session import SessionLocal, init_db
from app.demo.scenarios import get_demo_scenario
from app.jira.client import JiraClient
from app.jira.parser import detect_author_role, extract_text
from app.llm.client import LlmClient
from app.llm.prompts import build_ticket_analysis_prompt
from app.retrieval.ranker import retrieve_similar_tickets
from app.services.suggestion_publisher import format_internal_note
from app.storage.tickets import get_agent_profile, replace_ticket_links, save_suggestion, upsert_ticket_from_jira


def analyze_ticket_manual(jira_key: str, dry_run: bool = True) -> dict[str, Any]:
    settings = get_settings()
    jira = JiraClient(
        base_url=settings.jira_base_url,
        email=settings.jira_email,
        api_token=settings.jira_api_token,
    )
    llm = LlmClient(
        base_url=settings.groq_base_url if settings.llm_provider == "groq" else settings.llm_base_url,
        model=settings.llm_model,
        timeout=settings.llm_timeout_seconds,
        provider=settings.llm_provider,
        api_key=settings.groq_api_key if settings.llm_provider == "groq" else None,
    )
    session = None
    if not dry_run:
        init_db()
        session = SessionLocal()
    try:
        issue = jira.get_issue(
            jira_key,
            fields=[
                "project",
                "summary",
                "description",
                "comment",
                "assignee",
                "reporter",
                "status",
                "priority",
                "issuetype",
                "labels",
                "created",
                "updated",
            ],
        )
        comments_payload = jira.get_comments(jira_key)

        if dry_run:
            preview = _build_preview_data(issue, comments_payload)
            similar: list[dict[str, Any]] = []
            agent_profile = None
            summary = preview["summary"]
            description = preview["description"]
            comments = preview["comments"]
            ticket_id = None
        else:
            assert session is not None
            ticket = upsert_ticket_from_jira(session, issue, comments_payload)
            similar = retrieve_similar_tickets(session, ticket)
            replace_ticket_links(session, ticket, similar)
            agent_profile = get_agent_profile(session, ticket.assignee_display_name)
            comments = [
                {
                    "author_name": message.author_name,
                    "author_role": message.author_role,
                    "body": message.body_clean or "",
                }
                for message in sorted(
                    ticket.messages,
                    key=lambda item: item.created_at_jira or item.updated_at_jira or ticket.updated_at_jira,
                )
            ]
            summary = ticket.summary or ""
            description = ticket.description_clean or ""
            ticket_id = ticket.id

        prompt = build_ticket_analysis_prompt(
            jira_key=jira_key,
            summary=summary,
            description=description,
            comments=comments,
            similar_tickets=similar,
            agent_profile=agent_profile,
        )
        result = llm.generate_json(prompt)
        note = format_internal_note(result, similar)

        published = False
        jira_comment_id = None
        suggestion_id = None

        if not dry_run and settings.enable_jira_comment_publish:
            jira_comment = jira.add_comment(jira_key, note)
            jira_comment_id = jira_comment.get("id")
            published = True

        if not dry_run:
            assert session is not None
            suggestion = save_suggestion(
                session=session,
                ticket=ticket,
                model_name=settings.llm_model,
                result=result,
                internal_note=note,
                published_to_jira=published,
                jira_comment_id=jira_comment_id,
            )
            session.commit()
            suggestion_id = suggestion.id
        else:
            pass

        return {
            "jira_key": jira_key,
            "dry_run": dry_run,
            "ticket_id": ticket_id,
            "suggestion_id": suggestion_id,
            "result": result,
            "internal_note": note,
            "published_to_jira": published,
            "similar_tickets": similar,
        }
    finally:
        if session is not None:
            session.close()


def analyze_demo_ticket(scenario_id: str) -> dict[str, Any]:
    scenario = get_demo_scenario(scenario_id)
    if scenario is None:
        raise ValueError(f"Unknown demo scenario: {scenario_id}.")

    settings = get_settings()
    llm = LlmClient(
        base_url=settings.groq_base_url if settings.llm_provider == "groq" else settings.llm_base_url,
        model=settings.llm_model,
        timeout=settings.llm_timeout_seconds,
        provider=settings.llm_provider,
        api_key=settings.groq_api_key if settings.llm_provider == "groq" else None,
    )
    prompt = build_ticket_analysis_prompt(
        jira_key=scenario["ticket_key"],
        summary=scenario["summary"],
        description=scenario["description"],
        comments=scenario["comments"],
        similar_tickets=scenario["similar_tickets"],
        agent_profile=None,
    )
    result = llm.generate_json(prompt)
    note = format_internal_note(result, scenario["similar_tickets"])
    return {
        "scenario_id": scenario_id,
        "jira_key": scenario["ticket_key"],
        "dry_run": True,
        "result": result,
        "internal_note": note,
        "similar_tickets": scenario["similar_tickets"],
    }


def _build_preview_data(issue: dict[str, Any], comments_payload: dict[str, Any]) -> dict[str, Any]:
    fields = issue.get("fields", {})
    reporter = fields.get("reporter") or {}
    assignee = fields.get("assignee") or {}
    description = " ".join(extract_text(fields.get("description")).split())
    comments: list[dict[str, Any]] = []

    if description:
        comments.append(
            {
                "author_name": reporter.get("displayName"),
                "author_role": "customer",
                "body": description,
            }
        )

    for comment in comments_payload.get("comments", []):
        author = comment.get("author") or {}
        comments.append(
            {
                "author_name": author.get("displayName"),
                "author_role": detect_author_role(
                    author_account_id=author.get("accountId"),
                    reporter_account_id=reporter.get("accountId"),
                    assignee_account_id=assignee.get("accountId"),
                ),
                "body": " ".join(extract_text(comment.get("body")).split()),
            }
        )

    return {
        "summary": fields.get("summary", ""),
        "description": description,
        "comments": comments,
    }
