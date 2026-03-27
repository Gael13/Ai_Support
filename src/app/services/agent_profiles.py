from __future__ import annotations

from sqlalchemy import select

from app.db.models import AgentProfile
from app.db.session import SessionLocal, init_db


def list_agent_profiles() -> list[dict]:
    init_db()
    session = SessionLocal()
    try:
        profiles = session.execute(select(AgentProfile).order_by(AgentProfile.agent_name.asc())).scalars().all()
        return [
            {
                "agent_name": profile.agent_name,
                "agent_account_id": profile.agent_account_id,
                "source_ticket_count": profile.source_ticket_count,
                "style_rules": profile.style_rules_json or {},
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            }
            for profile in profiles
        ]
    finally:
        session.close()
