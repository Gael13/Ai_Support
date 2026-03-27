from __future__ import annotations

from typing import Any


def build_demo_report_payload(result: dict[str, Any]) -> dict[str, Any]:
    analysis = result.get("result", {}).get("analysis", {})
    sections = {
        "overview": {
            "scenario_id": result.get("scenario_id"),
            "jira_key": result.get("jira_key"),
            "first_impression": analysis.get("first_impression"),
            "confidence": result.get("result", {}).get("confidence"),
        },
        "analysis": {
            "issue_type": analysis.get("issue_type"),
            "observations": analysis.get("observations", []),
            "hypotheses": analysis.get("hypotheses", []),
            "missing_information": analysis.get("missing_information", []),
            "prevention_actions": analysis.get("prevention_actions", []),
            "risk_level": analysis.get("risk_level"),
        },
        "related_tickets": result.get("similar_tickets", []),
        "related_docs": result.get("result", {}).get("related_docs", []) or result.get("related_docs", []),
        "reply_fr": result.get("result", {}).get("suggested_reply_fr"),
        "reply_en": result.get("result", {}).get("suggested_reply_en"),
        "internal_note": result.get("internal_note"),
        "logs": result.get("logs", []),
        "agent_profile": result.get("agent_profile", {}),
    }
    return {
        "scenario_id": result.get("scenario_id"),
        "jira_key": result.get("jira_key"),
        "title": result.get("jira_key"),
        "sections": sections,
        "rendered_text": render_demo_report_text(sections),
    }


def render_demo_report_text(sections: dict[str, Any]) -> str:
    lines: list[str] = []
    overview = sections["overview"]
    analysis = sections["analysis"]

    lines.append("AI Demo Report")
    lines.append("")
    lines.append("Overview")
    lines.append(f"- Ticket: {overview.get('jira_key')}")
    if overview.get("first_impression"):
        lines.append(f"- First impression: {overview.get('first_impression')}")
    lines.append(f"- Confidence: {overview.get('confidence')}")

    lines.append("")
    lines.append("Analysis")
    if analysis.get("issue_type"):
        lines.append(f"- Issue type: {analysis.get('issue_type')}")
    for item in analysis.get("observations", []):
        lines.append(f"- Observation: {item}")
    for item in analysis.get("hypotheses", []):
        lines.append(f"- Hypothesis: {item}")
    for item in analysis.get("missing_information", []):
        lines.append(f"- Missing information: {item}")
    for item in analysis.get("prevention_actions", []):
        lines.append(f"- Prevention: {item}")

    lines.append("")
    lines.append("Related tickets")
    for item in sections.get("related_tickets", []):
        lines.append(f"- {item.get('jira_key')} ({item.get('score')}) - {item.get('reason')}")

    lines.append("")
    lines.append("Related documentation")
    for item in sections.get("related_docs", []):
        lines.append(f"- {item.get('title')} - {item.get('path')} - {item.get('reason')}")

    reply_fr = sections.get("reply_fr")
    if reply_fr:
        lines.append("")
        lines.append("Reply draft FR")
        lines.append(reply_fr)

    reply_en = sections.get("reply_en")
    if reply_en:
        lines.append("")
        lines.append("Reply draft EN")
        lines.append(reply_en)

    note = sections.get("internal_note")
    if note:
        lines.append("")
        lines.append("Internal note")
        lines.append(note)

    logs = sections.get("logs", [])
    if logs:
        lines.append("")
        lines.append("Logs")
        for item in logs:
            lines.append(f"- {item.get('step')}: {item.get('status')} - {item.get('details')}")

    return "\n".join(lines)
