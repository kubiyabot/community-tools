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
    python -m venv /opt/venv > /dev/null
    . /opt/venv/bin/activate > /dev/null
    pip install requests==2.32.3 2>&1 | grep -v '[notice]'

    # Run the access request handler script
    python /opt/scripts/access_request_handler.py "{{ .request_id }}" "{{ .ttl }}"
    """,
    args=[
        Arg(
            name="request_id",
            description=(
                "Unique identifier for the access request. This is used to track the request and match it with the approval decision."
            ),
            required=True,
        ),
        Arg(
            name="ttl",
            description=(
                "Desired time-to-live for the access (optional). Specifies for how long the access should be granted (not guaranteed as the approver may override). "
                "*Example*: `1h` for one hour, `30m` for 30 minutes."
            ),
            required=False,
            default="1h",
        ),
    ],
    env=[
        "REQUEST_ACCESS_WEBHOOK_URL",
    ],
    secrets=[
        "SLACK_API_TOKEN",
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/access_request_handler.py",
            content=inspect.getsource(access_request_handler),
        ),
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

__all__ = ["request_access_tool"]
