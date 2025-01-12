import inspect
import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kubiya_sdk.tools import Arg, FileSpec, Volume
from kubiya_sdk.tools.registry import tool_registry

from .base import JustInTimeAccessTool

# Read the search_access_requests script content directly from file
scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
with open(scripts_dir / "search_access_requests.py", "r") as f:
    script_content = f.read()

search_access_requests_tool = JustInTimeAccessTool(
    name="search_access_requests",
    description="Search for access requests based on status and/or tool name.",
    content="""
    set -e
    python /opt/scripts/search_access_requests.py "{{ .status }}" "{{ .tool_name }}"
    """,
    args=[
        Arg(
            name="status",
            description="Filter by request status (pending, approved, rejected).",
            required=False
        ),
        Arg(
            name="tool_name",
            description="Filter by tool name (partial matches are supported).",
            required=False
        ),
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/search_access_requests.py",
            content=script_content,
        ),
    ],
    with_volumes=[
        Volume(
            name="db_data",
            path="/var/lib/database"
        )
    ],
)

tool_registry.register("just_in_time_access", search_access_requests_tool)
__all__ = ['search_access_requests_tool']