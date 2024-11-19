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
from scripts import list_active_access_requests as list_requests_script

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
            content=inspect.getsource(list_requests_script),
        ),
    ],
)

# Register the tool
tool_registry.register("just_in_time_access", list_active_access_requests_tool)

__all__ = ["list_active_access_requests_tool"]
