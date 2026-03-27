from __future__ import annotations

from typing import Any


def build_ticket_analysis_prompt(
    jira_key: str,
    summary: str,
    description: str,
    comments: list[dict[str, Any]],
    similar_tickets: list[dict[str, Any]],
    related_docs: list[dict[str, Any]] | None = None,
    agent_profile: dict[str, Any] | None = None,
) -> str:
    conversation = "\n".join(
        f"[{item.get('author_role', 'unknown')}] {item.get('author_name', 'unknown')}: {item.get('body', '')}"
        for item in comments[-12:]
    )
    related = "\n".join(
        f"- {item['jira_key']} | score={item['score']:.2f} | reason={item['reason']}"
        for item in similar_tickets
    )
    docs = "\n".join(
        f"- {item['title']} | path={item['path']} | reason={item['reason']}"
        for item in (related_docs or [])
    )
    style = agent_profile or {
        "tone": "professional, calm, precise",
        "structure": [
            "acknowledge issue",
            "state current understanding",
            "ask precise follow-up questions",
            "propose next action",
        ],
        "avoid": ["unsupported certainty", "vague troubleshooting"],
    }
    return f"""
You are an internal support assistant for TheHive support tickets.

Rules:
- use only information supported by the ticket content and related tickets
- never invent a root cause
- separate observations, hypotheses, and missing information
- adapt the reply to the agent profile
- provide customer-facing drafts in French and English
- include a first impression and prevention guidance
- return strict JSON only

Ticket key: {jira_key}
Summary: {summary}
Description:
{description}

Conversation:
{conversation}

Similar tickets:
{related}

Related documentation:
{docs}

Agent profile:
{style}

Return:
{{
  "analysis": {{
    "issue_type": "",
    "first_impression": "",
    "observations": [],
    "hypotheses": [],
    "missing_information": [],
    "prevention_actions": [],
    "risk_level": "low|medium|high"
  }},
  "related_tickets": [
    {{"key": "", "score": 0.0, "reason": ""}}
  ],
  "related_docs": [
    {{"title": "", "path": "", "reason": ""}}
  ],
  "suggested_reply_fr": "",
  "suggested_reply_en": "",
  "internal_note": "",
  "confidence": 0.0
}}
""".strip()
