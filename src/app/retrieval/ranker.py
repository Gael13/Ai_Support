from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Ticket
from app.storage.tickets import normalize_text


def retrieve_similar_tickets(session: Session, ticket: Ticket, limit: int = 5) -> list[dict[str, Any]]:
    query_text = normalize_text(" ".join(filter(None, [ticket.summary, ticket.description_clean]))).lower()
    if not query_text:
        return []

    query_terms = set(query_text.split())
    candidates: list[dict[str, Any]] = []
    others = session.execute(select(Ticket).where(Ticket.id != ticket.id)).scalars().all()
    for other in others:
        other_text = normalize_text(" ".join(filter(None, [other.summary, other.description_clean]))).lower()
        if not other_text:
            continue
        other_terms = set(other_text.split())
        common_terms = query_terms & other_terms
        if not common_terms:
            continue
        score = min(len(common_terms) / 12.0, 0.6)
        reasons: list[str] = ["lexical_overlap"]
        if ticket.issue_type and other.issue_type and ticket.issue_type == other.issue_type:
            score += 0.15
            reasons.append("same_issue_type")
        if ticket.priority and other.priority and ticket.priority == other.priority:
            score += 0.05
            reasons.append("same_priority")
        if set(ticket.labels or []) & set(other.labels or []):
            score += 0.1
            reasons.append("shared_labels")
        candidates.append(
            {
                "jira_key": other.jira_key,
                "score": round(min(score, 0.99), 3),
                "reason": ", ".join(reasons),
            }
        )
    return sorted(candidates, key=lambda item: item["score"], reverse=True)[:limit]
