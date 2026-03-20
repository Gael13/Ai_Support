from __future__ import annotations

from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from app.core.errors import DependencyUnavailableError, UpstreamRequestError


class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(email, api_token)
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def search_issues(self, jql: str, fields: list[str], max_results: int = 50) -> dict[str, Any]:
        url = f"{self.base_url}/rest/api/3/search/jql"
        return self._perform_request(
            "get",
            url,
            params={"jql": jql, "maxResults": max_results, "fields": ",".join(fields)},
        )

    def get_issue(self, issue_key: str, fields: list[str] | None = None) -> dict[str, Any]:
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        return self._perform_request("get", f"{self.base_url}/rest/api/3/issue/{issue_key}", params=params)

    def get_comments(self, issue_key: str) -> dict[str, Any]:
        return self._perform_request("get", f"{self.base_url}/rest/api/3/issue/{issue_key}/comment")

    def add_comment(self, issue_key: str, body: str) -> dict[str, Any]:
        return self._perform_request(
            "post",
            f"{self.base_url}/rest/api/3/issue/{issue_key}/comment",
            json={
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": body}],
                        }
                    ],
                }
            },
        )

    def _perform_request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self.session.request(method=method, url=url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as exc:
            raise DependencyUnavailableError(
                message="Jira inaccessible",
                status_code=503,
                details={
                    "service": "jira",
                    "base_url": self.base_url,
                    "hint": "Verifier JIRA_BASE_URL, le reseau et l'acces a Jira.",
                },
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise DependencyUnavailableError(
                message="Jira ne repond pas a temps",
                status_code=504,
                details={
                    "service": "jira",
                    "base_url": self.base_url,
                    "hint": "Verifier la disponibilite Jira ou augmenter le timeout.",
                },
            ) from exc
        except requests.exceptions.HTTPError as exc:
            response = exc.response
            upstream_status = response.status_code if response is not None else 502
            details = {
                "service": "jira",
                "base_url": self.base_url,
                "upstream_status": upstream_status,
            }
            if upstream_status == 401:
                details["hint"] = "Verifier JIRA_EMAIL et JIRA_API_TOKEN."
            elif upstream_status == 403:
                details["hint"] = "Le compte Jira n'a pas les droits necessaires."
            elif upstream_status == 404:
                details["hint"] = "Verifier la cle ticket Jira ou l'endpoint utilise."
            raise UpstreamRequestError(
                message="Jira a repondu avec une erreur",
                status_code=upstream_status,
                details=details,
            ) from exc
