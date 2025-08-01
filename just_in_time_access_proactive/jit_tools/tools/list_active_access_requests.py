import inspect
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kubiya_workflow_sdk.tools import Arg, FileSpec, Volume
from kubiya_workflow_sdk.tools.registry import tool_registry

from .base import JustInTimeAccessTool

# Read the list_active_access_requests_handler script content directly from file
scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
with open(scripts_dir / "list_active_access_requests_handler.py", "r") as f:
    script_content = f.read()

list_active_access_requests_tool = JustInTimeAccessTool(
    name="list_active_access_requests",
    description="List all active access requests in the system.",
    content="""
    set -e
    python -m venv /opt/venv > /dev/null
    . /opt/venv/bin/activate > /dev/null
    pip install requests==2.32.3 2>&1 | grep -v '[notice]'
    python /opt/scripts/list_active_access_requests.py
    """,
    with_files=[
        FileSpec(
            destination="/opt/scripts/list_active_access_requests.py",
            content=script_content,
        ),
    ],
)

# Register the tool
tool_registry.register("just_in_time_access", list_active_access_requests_tool)

__all__ = ["list_active_access_requests_tool"]