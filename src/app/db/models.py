from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    jira_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    jira_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    project_key: Mapped[str | None] = mapped_column(String(64), index=True)
    issue_type: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str | None] = mapped_column(String(128), index=True)
    priority: Mapped[str | None] = mapped_column(String(128))
    assignee_account_id: Mapped[str | None] = mapped_column(String(128), index=True)
    assignee_display_name: Mapped[str | None] = mapped_column(String(255), index=True)
    reporter_account_id: Mapped[str | None] = mapped_column(String(128))
    reporter_display_name: Mapped[str | None] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)
    description_raw: Mapped[str | None] = mapped_column(Text)
    description_clean: Mapped[str | None] = mapped_column(Text)
    labels: Mapped[list[str] | None] = mapped_column(JSON, default=list)
    raw_payload: Mapped[dict | None] = mapped_column(JSON)
    created_at_jira: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    updated_at_jira: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_customer_comment_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_agent_comment_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    messages: Mapped[list["TicketMessage"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")
    suggestions: Mapped[list["TicketSuggestion"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")


class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    jira_comment_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    source_type: Mapped[str] = mapped_column(String(32))
    author_name: Mapped[str | None] = mapped_column(String(255), index=True)
    author_account_id: Mapped[str | None] = mapped_column(String(128), index=True)
    author_role: Mapped[str | None] = mapped_column(String(32), index=True)
    body_raw: Mapped[str | None] = mapped_column(Text)
    body_clean: Mapped[str | None] = mapped_column(Text)
    created_at_jira: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    updated_at_jira: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict | None] = mapped_column(JSON)

    ticket: Mapped["Ticket"] = relationship(back_populates="messages")

    __table_args__ = (
        UniqueConstraint("ticket_id", "source_type", "jira_comment_id", name="uq_ticket_message_jira"),
    )


class TicketSuggestion(Base):
    __tablename__ = "ticket_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    model_name: Mapped[str] = mapped_column(String(128), index=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    confidence: Mapped[float | None] = mapped_column(Float)
    analysis_json: Mapped[dict | None] = mapped_column(JSON)
    draft_reply: Mapped[str | None] = mapped_column(Text)
    internal_note: Mapped[str | None] = mapped_column(Text)
    published_to_jira: Mapped[bool] = mapped_column(Boolean, default=False)
    jira_comment_id: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    ticket: Mapped["Ticket"] = relationship(back_populates="suggestions")


class TicketLinkAI(Base):
    __tablename__ = "ticket_links_ai"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    linked_ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    score: Mapped[float] = mapped_column(Float, index=True)
    reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AgentProfile(Base):
    __tablename__ = "agent_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_account_id: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    agent_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    style_rules_json: Mapped[dict | None] = mapped_column(JSON)
    source_ticket_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
