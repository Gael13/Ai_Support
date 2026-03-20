from __future__ import annotations

from sqlalchemy import select

from app.db.models import Ticket
from app.db.session import SessionLocal, init_db
from app.services.analyze_ticket import analyze_ticket_manual


def analyze_recent_tickets_job() -> dict:
    init_db()
    session = SessionLocal()
    try:
        statement = (
            select(Ticket)
            .where(Ticket.last_customer_comment_at.is_not(None))
            .order_by(Ticket.updated_at_jira.desc())
            .limit(5)
        )
        tickets = session.execute(statement).scalars().all()
        ticket_keys = [ticket.jira_key for ticket in tickets]
    finally:
        session.close()

    analyzed: list[str] = []
    for jira_key in ticket_keys:
        analyze_ticket_manual(jira_key)
        analyzed.append(jira_key)
    return {"status": "ok", "analyzed": analyzed}
