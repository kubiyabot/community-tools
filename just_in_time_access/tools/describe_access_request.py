import inspect
from kubiya_sdk.tools import Arg, FileSpec, Volume
from just_in_time_access.tools.base import JustInTimeAccessTool
from kubiya_sdk.tools.registry import tool_registry
import just_in_time_access.scripts.describe_access_request as describe_access_request_script

describe_access_request_tool = JustInTimeAccessTool(
    name="describe_access_request",
    description="Describe a specific access request by its Request ID.",
    content="""
    set -e

    # Run the describe_access_request script
    python /opt/scripts/describe_access_request.py "{{ .request_id }}"
    """,
    args=[
        Arg(
            name="request_id",
            description="The Request ID to describe. Example: 'req-12345'.",
            required=True
        ),
    ],
    env=[
        "KUBIYA_USER_EMAIL",
    ],
    secrets=[
        "SLACK_API_TOKEN",
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/describe_access_request.py",
            content=inspect.getsource(describe_access_request_script),
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

        U ->> S: Request description of access request
        S -->> U: Display access request details
    """,
)

# Register the tool
tool_registry.register("just_in_time_access", describe_access_request_tool) 