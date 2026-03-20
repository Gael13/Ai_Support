from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import AgentProfile, Ticket, TicketLinkAI, TicketMessage, TicketSuggestion, utcnow
from app.jira.parser import detect_author_role, extract_text, parse_jira_datetime


def upsert_ticket_from_jira(session: Session, issue: dict[str, Any], comments_payload: dict[str, Any]) -> Ticket:
    fields = issue.get("fields", {})
    jira_key = issue["key"]
    ticket = session.execute(select(Ticket).where(Ticket.jira_key == jira_key)).scalar_one_or_none()
    if ticket is None:
        ticket = Ticket(jira_key=jira_key)
        session.add(ticket)

    reporter = fields.get("reporter") or {}
    assignee = fields.get("assignee") or {}
    description_text = extract_text(fields.get("description"))

    ticket.jira_id = issue.get("id")
    ticket.project_key = (fields.get("project") or {}).get("key")
    ticket.issue_type = (fields.get("issuetype") or {}).get("name")
    ticket.status = (fields.get("status") or {}).get("name")
    ticket.priority = (fields.get("priority") or {}).get("name")
    ticket.assignee_account_id = assignee.get("accountId")
    ticket.assignee_display_name = assignee.get("displayName")
    ticket.reporter_account_id = reporter.get("accountId")
    ticket.reporter_display_name = reporter.get("displayName")
    ticket.summary = fields.get("summary")
    ticket.description_raw = description_text
    ticket.description_clean = normalize_text(description_text)
    ticket.labels = fields.get("labels") or []
    ticket.raw_payload = issue
    ticket.created_at_jira = parse_jira_datetime(fields.get("created"))
    ticket.updated_at_jira = parse_jira_datetime(fields.get("updated"))
    ticket.last_synced_at = utcnow()

    _replace_ticket_messages(session, ticket, description_text, comments_payload)
    _refresh_last_message_timestamps(ticket)
    session.flush()
    return ticket


def save_suggestion(
    session: Session,
    ticket: Ticket,
    model_name: str,
    result: dict[str, Any],
    internal_note: str,
    published_to_jira: bool,
    jira_comment_id: str | None = None,
) -> TicketSuggestion:
    suggestion = TicketSuggestion(
        ticket=ticket,
        model_name=model_name,
        prompt_version="v1",
        confidence=result.get("confidence"),
        analysis_json=result,
        draft_reply=result.get("suggested_reply"),
        internal_note=internal_note,
        published_to_jira=published_to_jira,
        jira_comment_id=jira_comment_id,
    )
    session.add(suggestion)
    session.flush()
    return suggestion


def replace_ticket_links(session: Session, ticket: Ticket, similar_items: list[dict[str, Any]]) -> None:
    session.execute(delete(TicketLinkAI).where(TicketLinkAI.source_ticket_id == ticket.id))
    for item in similar_items:
        linked_ticket = session.execute(select(Ticket).where(Ticket.jira_key == item["jira_key"])).scalar_one_or_none()
        if linked_ticket is None:
            continue
        session.add(
            TicketLinkAI(
                source_ticket_id=ticket.id,
                linked_ticket_id=linked_ticket.id,
                score=item["score"],
                reason=item["reason"],
            )
        )


def get_agent_profile(session: Session, agent_name: str | None) -> dict[str, Any] | None:
    if not agent_name:
        return None
    profile = session.execute(select(AgentProfile).where(AgentProfile.agent_name == agent_name)).scalar_one_or_none()
    if profile is None:
        return None
    return profile.style_rules_json


def _replace_ticket_messages(session: Session, ticket: Ticket, description_text: str, comments_payload: dict[str, Any]) -> None:
    existing = session.execute(select(TicketMessage).where(TicketMessage.ticket_id == ticket.id)).scalars().all()
    for message in existing:
        session.delete(message)

    if description_text:
        session.add(
            TicketMessage(
                ticket=ticket,
                jira_comment_id=None,
                source_type="description",
                author_name=ticket.reporter_display_name,
                author_account_id=ticket.reporter_account_id,
                author_role="customer",
                body_raw=description_text,
                body_clean=normalize_text(description_text),
                created_at_jira=ticket.created_at_jira,
                updated_at_jira=ticket.updated_at_jira,
                raw_payload={"source": "description"},
            )
        )

    for comment in comments_payload.get("comments", []):
        author = comment.get("author") or {}
        body_raw = extract_text(comment.get("body"))
        session.add(
            TicketMessage(
                ticket=ticket,
                jira_comment_id=comment.get("id"),
                source_type="comment",
                author_name=author.get("displayName"),
                author_account_id=author.get("accountId"),
                author_role=detect_author_role(
                    author_account_id=author.get("accountId"),
                    reporter_account_id=ticket.reporter_account_id,
                    assignee_account_id=ticket.assignee_account_id,
                ),
                body_raw=body_raw,
                body_clean=normalize_text(body_raw),
                created_at_jira=parse_jira_datetime(comment.get("created")),
                updated_at_jira=parse_jira_datetime(comment.get("updated")),
                raw_payload=comment,
            )
        )


def _refresh_last_message_timestamps(ticket: Ticket) -> None:
    customer_timestamps = [m.created_at_jira for m in ticket.messages if m.author_role == "customer" and m.created_at_jira]
    agent_timestamps = [m.created_at_jira for m in ticket.messages if m.author_role == "support" and m.created_at_jira]
    ticket.last_customer_comment_at = max(customer_timestamps) if customer_timestamps else None
    ticket.last_agent_comment_at = max(agent_timestamps) if agent_timestamps else None


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.split())
