import inspect
import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kubiya_sdk.tools import Arg, FileSpec, Volume
from kubiya_sdk.tools.registry import tool_registry

from .base import JustInTimeAccessTool
from scripts import view_user_requests as view_user_requests_script

view_user_requests_tool = JustInTimeAccessTool(
    name="view_user_requests",
    description="View all access requests for a specific user.",
    content="""
    set -e
    python /opt/scripts/view_user_requests.py "{{ .user_email }}"
    """,
    args=[
        Arg(
            name="user_email",
            description="The email address of the user whose requests to view.",
            required=True
        ),
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/view_user_requests.py",
            content=inspect.getsource(view_user_requests_script),
        ),
    ],
    with_volumes=[
        Volume(
            name="db_data",
            path="/var/lib/database"
        )
    ],
)

tool_registry.register("just_in_time_access", view_user_requests_tool)
__all__ = ['view_user_requests_tool'] 