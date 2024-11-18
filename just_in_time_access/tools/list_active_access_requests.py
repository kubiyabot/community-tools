import inspect
from kubiya_sdk.tools import FileSpec, Volume
from just_in_time_access.tools.base import JustInTimeAccessTool
from kubiya_sdk.tools.registry import tool_registry
import just_in_time_access.scripts.list_active_access_requests as list_active_requests_script

list_active_access_requests_tool = JustInTimeAccessTool(
    name="list_active_access_requests",
    description="List all active (pending) access requests.",
    content="""
    #!/bin/bash
    set -e

    # Run the list_active_access_requests script
    python /opt/scripts/list_active_access_requests.py
    """,
    env=[
        "KUBIYA_USER_EMAIL",
    ],
    secrets=[
        "SLACK_API_TOKEN",
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/list_active_access_requests.py",
            content=inspect.getsource(list_active_requests_script),
        ),
    ],
    with_volumes=[
        Volume(
            name="db_data",
            path="/var/lib/database"
        )
    ],
    long_running=False,
    mermaid="""
    sequenceDiagram
        participant U as User
        participant S as System

        U ->> S: List active access requests
        S -->> U: Display list of active requests
    """,
)

# Register the tool
tool_registry.register("just_in_time_access", list_active_access_requests_tool) 