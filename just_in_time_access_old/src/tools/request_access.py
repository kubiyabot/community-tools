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
        "Request temporary access to a tool or resource that failed due to missing permissions. "
        "NOTE: You typically won't need to run this tool directly - it can be used when another tool fails due to insufficient permissions."
        "On failure, you'll see an error message containing a 'Request ID'. ASK THE USER if he wants to submit an access request for the operation. Do not assume."
    ),
    content="""
    set -e
    echo "🚀 Submitting your access request..."
    echo "⏳ Please wait while we process your request..."
    python -m venv /opt/venv > /dev/null
    . /opt/venv/bin/activate > /dev/null
    pip install requests==2.32.3 2>&1 | grep -v '[notice]' > /dev/null

    # Run the access request handler script
    python /opt/scripts/access_request_handler.py "{{ .request_id }}" "{{ .ttl }}"
    """,
    args=[
        Arg(
            name="request_id",
            description=(
                "The unique identifier for this access request. "
                "This is automatically provided when a tool fails due to permissions - "
                "you'll see it in the error message like: 'Access denied. Request ID: abc-123'. "
                "Use that ID when running this tool."
            ),
            required=True,
        ),
        Arg(
            name="ttl",
            description=(
                "How long you need the access for. The approver may adjust this duration.\n"
                "Examples:\n"
                "- '1h' for one hour access\n" 
                "- '30m' for 30 minutes access\n"
                "- '2h' for two hours access"
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
