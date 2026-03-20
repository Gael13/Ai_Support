from __future__ import annotations

from typing import Any


def build_ticket_analysis_prompt(
    jira_key: str,
    summary: str,
    description: str,
    comments: list[dict[str, Any]],
    similar_tickets: list[dict[str, Any]],
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
- return strict JSON only

Ticket key: {jira_key}
Summary: {summary}
Description:
{description}

Conversation:
{conversation}

Similar tickets:
{related}

Agent profile:
{style}

Return:
{{
  "analysis": {{
    "issue_type": "",
    "observations": [],
    "hypotheses": [],
    "missing_information": [],
    "risk_level": "low|medium|high"
  }},
  "related_tickets": [
    {{"key": "", "score": 0.0, "reason": ""}}
  ],
  "suggested_reply": "",
  "internal_note": "",
  "confidence": 0.0
}}
""".strip()
