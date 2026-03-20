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
            {
                "jira_key": "DEMO-1842",
                "score": 0.93,
                "reason": "same_symptom, same_topology, same_memory_pressure",
            },
            {
                "jira_key": "DEMO-2091",
                "score": 0.88,
                "reason": "same_outofmemoryerror, shared_services_on_single_host",
            },
        ],
    }
}


def list_demo_scenarios() -> list[dict[str, str]]:
    return [
        {"scenario_id": scenario_id, "ticket_key": scenario["ticket_key"], "summary": scenario["summary"]}
        for scenario_id, scenario in DEMO_SCENARIOS.items()
    ]


def get_demo_scenario(scenario_id: str) -> dict[str, Any] | None:
    return DEMO_SCENARIOS.get(scenario_id)
