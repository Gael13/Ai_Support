from __future__ import annotations

from typing import Any


DEMO_SCENARIOS: dict[str, dict[str, Any]] = {
    "thehive-oom-16gb": {
        "ticket_key": "DEMO-THEHIVE-OOM-16GB",
        "summary": "TheHive crashes with OutOfMemoryError on a 16 GB host running TheHive, Cassandra, Elasticsearch and Cortex",
        "description": (
            "We have a single Ubuntu VM with 16 GB RAM hosting TheHive, Cassandra, Elasticsearch and Cortex. "
            "TheHive becomes slow after a few hours, then the service crashes. In the logs we can see "
            "'java.lang.OutOfMemoryError: Java heap space'. After restart it works again for some time. "
            "Current deployment is all-in-one on the same host. We need help to understand the cause and "
            "what should be changed to avoid another crash."
        ),
        "comments": [
            {
                "author_name": "Customer",
                "author_role": "customer",
                "body": (
                    "The host has 16 GB RAM total. Cassandra, Elasticsearch, TheHive and Cortex are on the same VM. "
                    "We set TheHive heap to 8G because we thought more heap would help. Elasticsearch has 4G heap. "
                    "Cortex is also running locally. The crash happens mainly during busy mornings."
                ),
            },
            {
                "author_name": "Customer",
                "author_role": "customer",
                "body": (
                    "Around the crash we see long GC pauses and then OutOfMemoryError. "
                    "We did not yet collect a full thread dump. Swap is enabled and becomes active before the crash."
                ),
            },
        ],
        "similar_tickets": [
            {"jira_key": "DEMO-1842", "score": 0.93, "reason": "same_symptom, same_topology, same_memory_pressure"},
            {"jira_key": "DEMO-2091", "score": 0.88, "reason": "same_outofmemoryerror, shared_services_on_single_host"},
            {"jira_key": "DEMO-2217", "score": 0.82, "reason": "same_gc_pressure, same_swap_activity"},
        ],
        "related_docs": [
            {
                "title": "TheHive sizing guidance for single-node deployments",
                "path": "docs/thehive/sizing/single-node.md",
                "reason": "explains resource contention on all-in-one deployments",
            },
            {
                "title": "Runbook: Java OOM and GC troubleshooting",
                "path": "docs/runbooks/java-oom-gc.md",
                "reason": "covers heap sizing, GC pauses and prevention checks",
            },
        ],
    },
    "cortex-analyzer-timeout": {
        "ticket_key": "DEMO-CORTEX-TIMEOUT",
        "summary": "Cortex analyzers start timing out after upgrade and jobs remain in waiting state",
        "description": (
            "Since the last upgrade, several Cortex analyzers remain pending for a long time and then fail with timeout. "
            "TheHive can still create cases, but enrichment is delayed or missing. The issue is intermittent."
        ),
        "comments": [
            {
                "author_name": "Customer",
                "author_role": "customer",
                "body": (
                    "We are running Cortex with Docker. Some analyzers still work, but the heaviest ones now hit the timeout. "
                    "CPU usage is high during bursts. We also changed the reverse proxy configuration during the same maintenance window."
                ),
            }
        ],
        "similar_tickets": [
            {"jira_key": "DEMO-3104", "score": 0.91, "reason": "same_analyzer_timeout, same_docker_runtime"},
            {"jira_key": "DEMO-2877", "score": 0.79, "reason": "same_proxy_change, same_post_upgrade_regression"},
        ],
        "related_docs": [
            {
                "title": "Cortex job timeout tuning",
                "path": "docs/cortex/analyzers/timeouts.md",
                "reason": "documents timeout and worker tuning",
            },
            {
                "title": "Reverse proxy checklist for TheHive and Cortex",
                "path": "docs/platform/reverse-proxy-checklist.md",
                "reason": "useful because the incident started after proxy changes",
            },
        ],
    },
    "thehive-auth-proxy-loop": {
        "ticket_key": "DEMO-AUTH-PROXY-LOOP",
        "summary": "Users are redirected in a login loop after SSO is enabled behind reverse proxy",
        "description": (
            "After enabling SSO behind our reverse proxy, users authenticate successfully with the identity provider "
            "but then return to TheHive and are redirected back to login again. API calls sometimes work, but the UI is unusable."
        ),
        "comments": [
            {
                "author_name": "Customer",
                "author_role": "customer",
                "body": (
                    "The issue started immediately after we moved from direct access to an HTTPS reverse proxy. "
                    "We may have changed X-Forwarded headers and cookie settings at the same time."
                ),
            }
        ],
        "similar_tickets": [
            {"jira_key": "DEMO-4021", "score": 0.9, "reason": "same_sso_loop, same_proxy_headers"},
            {"jira_key": "DEMO-3975", "score": 0.84, "reason": "same_cookie_scope_issue, same_https_transition"},
        ],
        "related_docs": [
            {
                "title": "SSO deployment checklist behind reverse proxy",
                "path": "docs/thehive/auth/sso-proxy-checklist.md",
                "reason": "covers redirect URI, cookie and forwarded headers",
            },
            {
                "title": "Troubleshooting session cookies",
                "path": "docs/platform/auth/session-cookies.md",
                "reason": "relevant to login loop symptoms",
            },
        ],
    },
}


def list_demo_scenarios() -> list[dict[str, str]]:
    return [
        {"scenario_id": scenario_id, "ticket_key": scenario["ticket_key"], "summary": scenario["summary"]}
        for scenario_id, scenario in DEMO_SCENARIOS.items()
    ]


def get_demo_scenario(scenario_id: str) -> dict[str, Any] | None:
    return DEMO_SCENARIOS.get(scenario_id)
