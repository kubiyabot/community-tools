import inspect
from kubiya_sdk.tools import Arg, FileSpec, Volume
from .base import JustInTimeAccessTool
from kubiya_sdk.tools.registry import tool_registry
import sys
import os
from pathlib import Path

# Get the scripts directory path
SCRIPTS_DIR = Path(__file__).parent.parent.parent / 'scripts'
sys.path.append(str(SCRIPTS_DIR))

import describe_access_request as describe_access_request_script

describe_access_request_tool = JustInTimeAccessTool(
    name="describe_access_request",
    description="Describe a specific access request by its Request ID.",
    content="""
    set -e
    python /opt/scripts/describe_access_request.py "{{ .request_id }}"
    """,
    args=[
        Arg(
            name="request_id",
            description="The Request ID to describe. Example: 'req-12345'.",
            required=True
        ),
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
)

# Register the tool
tool_registry.register("just_in_time_access", describe_access_request_tool) 