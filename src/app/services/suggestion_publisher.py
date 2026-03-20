from __future__ import annotations

from typing import Any


def format_internal_note(result: dict[str, Any], similar: list[dict[str, Any]]) -> str:
    lines = ["[AI Support Assistant]", "", "Summary"]
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
    reply = result.get("suggested_reply")
    if reply:
        lines.append("")
        lines.append("Suggested reply draft")
        lines.append(reply)
    return "\n".join(lines)
