from __future__ import annotations

from typing import Any


def format_internal_note(result: dict[str, Any], similar: list[dict[str, Any]]) -> str:
    lines = ["[AI Support Assistant]", "", "Summary"]
    first_impression = result.get("analysis", {}).get("first_impression")
    if first_impression:
        lines.append(f"- First impression: {first_impression}")
    for observation in result.get("analysis", {}).get("observations", [])[:5]:
        lines.append(f"- {observation}")
    lines.append("")
    lines.append(f"Confidence: {result.get('confidence', 'n/a')}")
    lines.append("")
    lines.append("Similar past tickets")
    for item in similar[:5]:
        lines.append(f"- {item['jira_key']} ({item['score']}) - {item['reason']}")
    missing = result.get("analysis", {}).get("missing_information", [])
    if missing:
        lines.append("")
        lines.append("Missing information to request")
        for item in missing[:6]:
            lines.append(f"- {item}")
    prevention = result.get("analysis", {}).get("prevention_actions", [])
    if prevention:
        lines.append("")
        lines.append("Prevention actions")
        for item in prevention[:6]:
            lines.append(f"- {item}")
    docs = result.get("related_docs", [])
    if docs:
        lines.append("")
        lines.append("Related documentation")
        for item in docs[:5]:
            lines.append(f"- {item.get('title')} - {item.get('path')} - {item.get('reason')}")
    reply_fr = result.get("suggested_reply_fr")
    if reply_fr:
        lines.append("")
        lines.append("Suggested reply draft (FR)")
        lines.append(reply_fr)
    reply_en = result.get("suggested_reply_en")
    if reply_en:
        lines.append("")
        lines.append("Suggested reply draft (EN)")
        lines.append(reply_en)
    return "\n".join(lines)
