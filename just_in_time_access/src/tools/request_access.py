import inspect
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kubiya_sdk.tools import Arg, FileSpec, Volume
from kubiya_sdk.tools.registry import tool_registry

from .base import JustInTimeAccessTool
from scripts import access_request_handler

request_access_tool = JustInTimeAccessTool(
    name="request_tool_access",
    description=(
        "Initiate a request for temporary access to a specific tool or resource. "
        "This tool sends an access request to approvers and awaits approval."
    ),
    content="""
    set -e

    # Get tool name and params from environment variables
    TOOL_NAME="${KUBIYA_TOOL_NAME:-{{ .tool_name }}}"
    TOOL_PARAMS="${KUBIYA_TOOL_PARAMS:-{{ .tool_params }}}"

    # Run the access request handler script
    python /opt/scripts/access_request_handler.py "$TOOL_NAME" "{{ .user_email }}" "$TOOL_PARAMS" "{{ .ttl }}"
    """,
    args=[
        Arg(
            name="tool_name",
            description=(
                "The name of the tool which access is being requested.\n"
                "*Example*: `rollout_restart_deployment`, `restart_ecs_service`"
            ),
            required=True
        ),
        Arg(
            name="user_email",
            description=(
                "The email address of the user requesting access.\n"
                "*Example*: `user@example.com`."
            ),
            required=True
        ),
        Arg(
            name="tool_params",
            description=(
                "Additional parameters required by the tool or resource. Provide as a JSON-formatted string.\n"
                "*Example*: `{\"region\": \"us-east-1\", \"bucket_name\": \"my-bucket\"}`."
            ),
            required=True
        ),
        Arg(
            name="ttl",
            description=(
                "Desired time-to-live for the access (optional). Specifies for how long the access should be granted (not guaranteed as the approver may override). "
                "*Example*: `1h` for one hour, `30m` for 30 minutes."
            ),
            required=False,
            default="1h"
        ),
    ],
    env=[
        "SLACK_CHANNEL_ID",
        "KUBIYA_TOOL_NAME",
        "KUBIYA_TOOL_PARAMS",
    ],
    secrets=[
        "SLACK_API_KEY",
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/access_request_handler.py",
            content=inspect.getsource(access_request_handler),
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
        participant A as Approver

        U ->> S: Request Access
        S ->> A: Send Approval Request
        A -->> S: Approve/Reject
        S -->> U: Notify User
    """,
)

# Register the tool
tool_registry.register("just_in_time_access", request_access_tool)

__all__ = ['request_access_tool'] 