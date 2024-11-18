import inspect
from kubiya_sdk.tools import FileSpec, Volume
from just_in_time_access.src.tools.base import JustInTimeAccessTool
from kubiya_sdk.tools.registry import tool_registry
import sys
import os
from pathlib import Path

# Get the scripts directory path
SCRIPTS_DIR = Path(__file__).parent.parent.parent / 'scripts'
sys.path.append(str(SCRIPTS_DIR))

import list_active_access_requests as list_requests_script

list_active_access_requests_tool = JustInTimeAccessTool(
    name="list_active_access_requests",
    description="List all active (pending) access requests.",
    content="""
    set -e
    python /opt/scripts/list_active_access_requests.py
    """,
    with_files=[
        FileSpec(
            destination="/opt/scripts/list_active_access_requests.py",
            content=inspect.getsource(list_requests_script),
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
tool_registry.register("just_in_time_access", list_active_access_requests_tool) 