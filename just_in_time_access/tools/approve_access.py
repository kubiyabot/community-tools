import inspect
from kubiya_sdk.tools import Arg, FileSpec, Volume
from just_in_time_access.tools.base import JustInTimeAccessTool
from kubiya_sdk.tools.registry import tool_registry
import just_in_time_access.scripts.access_approval_handler as access_approval_handler

approve_access_tool = JustInTimeAccessTool(
    name="approve_tool_access_request",
    description=(
        "Handle the approval or rejection of an access request. "
        "This tool processes the approval action and notifies the requester."
    ),
    content="""
    #!/bin/bash
    set -e

    # Run the access approval handler script
    python /opt/scripts/access_approval_handler.py "{{ .request_id }}" "{{ .approval_action }}"
    """,
    args=[
        Arg(
            name="request_id",
            description=(
                "The unique identifier of the access request to be approved or rejected.\n"
                "*Example*: `req-12345`."
            ),
            required=True
        ),
        Arg(
            name="approval_action",
            description=(
                "The action to perform on the access request. Must be either `approve` or `reject`.\n"
                "*Example*: `approve`."
            ),
            required=True
        ),
    ],
    env=[
        "SLACK_CHANNEL_ID",
        "APPROVALS_CHANNEL_ID",
    ],
    secrets=[
        "SLACK_API_TOKEN",
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/access_approval_handler.py",
            content=inspect.getsource(access_approval_handler),
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
        participant A as Approver
        participant S as System
        participant U as User

        A ->> S: Approve Access
        S ->> LocalService: Send HTTP Request
        S -->> U: Notify User
    """,
)

# Register the tool
tool_registry.register("just_in_time_access", approve_access_tool) 