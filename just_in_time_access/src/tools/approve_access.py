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
from scripts import access_approval_handler

# Define the tool before any potential imports can occur
approve_access_tool = JustInTimeAccessTool(
    name="approve_tool_access_request",
    description=(
        "Handle the approval or rejection of an access request. "
        "This tool processes the approval action and notifies the requester."
    ),
    content="""
    set -e
    python -m venv /opt/venv > /dev/null
    . /opt/venv/bin/activate > /dev/null
    pip install requests==2.32.3 2>&1 | grep -v '[notice]'

    # Run the access approval handler script
    python /opt/scripts/access_approval_handler.py "{{ .request_id }}" "{{ .approval_action }}" "{{ .ttl }}"
    """,
    args=[
        Arg(
            name="request_id",
            description=(
                "The unique identifier of the access request to be approved or rejected.\n"
                "*Example*: `req-12345`."
            ),
            required=True,
        ),
        Arg(
            name="approval_action",
            description=(
                "The action to perform on the access request. Must be either `approve` or `reject`.\n"
                "*Example*: `approve`."
            ),
            required=True,
        ),
        Arg(
            name="ttl",
            description=(
                "Actual time-to-live for the access (optional). Specifies for how long the access should be granted (not guaranteed as the approver may override).\n"
                "*Example*: `1h` for one hour, `30m` for 30 minutes.\n"
                "This is only required if the approval action is `approve`."
            ),
            required=False,
        ),
    ],
    env=[
        "KUBIYA_AGENT_NAME",
        "SLACK_CHANNEL_ID",
    ],
    secrets=[
        "SLACK_API_TOKEN",
        "KUBIYA_API_KEY",
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/access_approval_handler.py",
            content=inspect.getsource(access_approval_handler),
        ),
    ],
    with_volumes=[Volume(name="db_data", path="/var/lib/database")],
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

# Export the tool
__all__ = ["approve_access_tool"]

# Make sure the tool is available at module level
globals()["approve_access_tool"] = approve_access_tool
