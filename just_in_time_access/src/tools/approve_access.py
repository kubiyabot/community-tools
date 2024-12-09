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
        "Handle the approval or rejection of an access request.\n"
        "NOTE: This tool requires special approver permissions - only designated approvers can use this tool.\n"
        "If you need to request access instead of approving it, use the 'request_tool_access' tool.\n"
        "This tool processes approval actions and automatically notifies requesters of the decision."
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
                "The unique identifier of the access request to process.\n"
                "*Example*: `req-12345`"
            ),
            required=True,
        ),
        Arg(
            name="approval_action",
            description=(
                "Your decision on the access request. Must be either:\n"
                "- `approve`: Grant the requested access\n"
                "- `reject`: Deny the access request\n"
                "*Example*: `approve`"
            ),
            required=True,
        ),
        Arg(
            name="ttl",
            description=(
                "If approving, specify how long the access should be valid for.\n"
                "This can be different from what was requested - you can increase or decrease the duration.\n"
                "Format: <number><unit> where unit is:\n"
                "- 'h' for hours\n"
                "- 'm' for minutes\n"
                "*Examples*:\n"
                "- `1h` for one hour\n"
                "- `30m` for 30 minutes\n"
                "- `4h` for four hours\n"
                "Only required when approval_action is `approve`"
            ),
            required=False,
        ),
    ],
    env=[
        "KUBIYA_AGENT_NAME",
        "SLACK_CHANNEL_ID",
        "KUBIYA_AGENT_UUID",
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
