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
from scripts import describe_access_request as describe_access_request_script

describe_access_request_tool = JustInTimeAccessTool(
    name="describe_access_request",
    description="Describe a specific access request by its Request ID.",
    content="""
    set -e
    python -m venv /opt/venv > /dev/null
    . /opt/venv/bin/activate > /dev/null
    pip install requests==2.32.3 2>&1 | grep -v '[notice]'
    python /opt/scripts/describe_access_request.py "{{ .request_id }}"
    """,
    args=[
        Arg(
            name="request_id",
            description="The Request ID to describe. Example: 'req-12345'.",
            required=True,
        ),
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/describe_access_request.py",
            content=inspect.getsource(describe_access_request_script),
        ),
    ],
)

# Register the tool
tool_registry.register("just_in_time_access", describe_access_request_tool)

__all__ = ["describe_access_request_tool"]
