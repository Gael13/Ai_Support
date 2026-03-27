from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.core.config import get_settings
from app.db.session import SessionLocal, init_db
from app.jira.client import JiraClient
from app.storage.tickets import upsert_ticket_from_jira


ISSUE_FIELDS = [
    "project",
    "summary",
    "description",
    "status",
    "updated",
    "created",
    "assignee",
    "reporter",
    "priority",
    "issuetype",
    "labels",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill Jira ticket history into the local database.")
    parser.add_argument("--project", default=None, help="Jira project key. Defaults to JIRA_PROJECT_KEY.")
    parser.add_argument("--jql", default=None, help="Override JQL query.")
    parser.add_argument("--batch-size", type=int, default=50, help="Number of issues per page.")
    parser.add_argument("--max-issues", type=int, default=0, help="Optional hard limit. 0 means all issues.")
    args = parser.parse_args()

    settings = get_settings()
    init_db()
    jira = JiraClient(
        base_url=settings.jira_base_url,
        email=settings.jira_email,
        api_token=settings.jira_api_token,
    )
    session = SessionLocal()
    try:
        project = args.project or settings.jira_project_key
        jql = args.jql or f"project = {project} ORDER BY created ASC"
        start_at = 0
        imported = 0
        while True:
            payload = jira.search_issues(
                jql=jql,
                fields=ISSUE_FIELDS,
                max_results=args.batch_size,
                start_at=start_at,
            )
            issues = payload.get("issues", [])
            if not issues:
                break

            for issue in issues:
                comments_payload = jira.get_comments(issue["key"])
                upsert_ticket_from_jira(session, issue, comments_payload)
                imported += 1
                print(f"[sync] imported {issue['key']} ({imported})")
                if args.max_issues and imported >= args.max_issues:
                    break

            session.commit()
            if args.max_issues and imported >= args.max_issues:
                break

            total = payload.get("total", 0)
            start_at += len(issues)
            print(f"[sync] page complete start_at={start_at} total={total}")
            if start_at >= total:
                break

        print(f"[done] imported={imported} jql={jql}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
