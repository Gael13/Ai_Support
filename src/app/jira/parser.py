from __future__ import annotations

from datetime import datetime
from typing import Any


def extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        parts: list[str] = []
        for item in value.get("content", []):
            parts.extend(_extract_from_adf_node(item))
        return " ".join(part for part in parts if part).strip()
    return str(value)


def parse_jira_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def detect_author_role(
    author_account_id: str | None,
    reporter_account_id: str | None,
    assignee_account_id: str | None,
) -> str:
    if author_account_id and reporter_account_id and author_account_id == reporter_account_id:
        return "customer"
    if author_account_id and assignee_account_id and author_account_id == assignee_account_id:
        return "support"
    return "unknown"


def _extract_from_adf_node(node: Any) -> list[str]:
    if not isinstance(node, dict):
        return []
    texts: list[str] = []
    if node.get("type") == "text":
        texts.append(node.get("text", ""))
    for child in node.get("content", []):
        texts.extend(_extract_from_adf_node(child))
    return texts
