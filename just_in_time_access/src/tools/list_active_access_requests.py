import inspect
import sys
from pathlib import Path

# Get the package root directory and add it to sys.path
PACKAGE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE_ROOT))

from kubiya_sdk.tools import FileSpec, Volume
from kubiya_sdk.tools.registry import tool_registry

# Use absolute imports
from just_in_time_access.src.tools.base import JustInTimeAccessTool
import just_in_time_access.scripts.list_active_access_requests as list_requests_script

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