import inspect
import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kubiya_sdk.tools import Arg, FileSpec
from kubiya_sdk.tools.registry import tool_registry

from .base import JustInTimeAccessTool
from scripts import search_access_requests as search_requests_script

search_access_requests_tool = JustInTimeAccessTool(
    name="search_access_requests",
    description="Search for access requests based on status, tool name, user, groups, and date ranges.",
    content="""
    set -e
    python -m venv /opt/venv > /dev/null
    . /opt/venv/bin/activate > /dev/null
    pip install requests==2.32.3 2>&1 | grep -v '[notice]'
    python /opt/scripts/search_access_requests.py \
        "{{ .status }}" \
        "{{ .tool_name }}" \
        {{ if .user_email }}--user_email "{{ .user_email }}"{{ end }} \
        {{ if .group }}--group "{{ .group }}"{{ end }} \
        {{ if .created_after }}--created_after "{{ .created_after }}"{{ end }} \
        {{ if .created_before }}--created_before "{{ .created_before }}"{{ end }}
    """,
    args=[
        Arg(
            name="status",
            description="Filter by request status (pending/approved)",
            required=False
        ),
        Arg(
            name="tool_name",
            description="Filter by tool name",
            required=False
        ),
        Arg(
            name="user_email",
            description="Filter by user email",
            required=False
        ),
        Arg(
            name="group",
            description="Filter by group name",
            required=False
        ),
        Arg(
            name="created_after",
            description="Filter requests created after date (YYYY-MM-DD)",
            required=False
        ),
        Arg(
            name="created_before",
            description="Filter requests created before date (YYYY-MM-DD)",
            required=False
        ),
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/search_access_requests.py",
            content=inspect.getsource(search_requests_script),
        ),
    ],
)

# Register the tool
tool_registry.register("just_in_time_access", search_access_requests_tool)

__all__ = ["search_access_requests_tool"]