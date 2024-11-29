import inspect
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kubiya_sdk.tools import Arg, FileSpec
from kubiya_sdk.tools.registry import tool_registry
from .base import MemoryManagementTool
from ..utils import get_script_files  # Import the utility function

list_memories_tool = MemoryManagementTool(
    name="list_memories",
    description=(
        "🎯 [Recommended First Step] View your stored preferences and settings!\n\n"
        "This tool shows all your stored preferences and settings, helping me understand your "
        "previous choices and preferences. Running this at the start of our conversation helps "
        "me provide more personalized assistance.\n\n"
        "You can optionally filter the results by providing search terms that match either the "
        "content or tags of your stored preferences."
    ),
    content="""
set -e
python -m venv /opt/venv > /dev/null
. /opt/venv/bin/activate > /dev/null
pip install mem0ai 2>&1 | grep -v '[notice]' > /dev/null

# Run the list memories handler script
python /opt/scripts/list_memories_handler.py {{ if .search_filter }}"{{ .search_filter }}"{{ end }} || exit 1
""",
    args=[
        Arg(
            name="search_filter",
            description=(
                "Optional search terms to filter your preferences. Matches against both content and tags.\n"
                "**Example**: \"notifications email\" will show preferences related to email notifications"
            ),
            required=False,
            default=None,
        ),
    ],
    env=[
        "KUBIYA_USER_EMAIL",
        "KUBIYA_USER_ORG",
        "NEO4J_URI",
        "NEO4J_USER",
    ],
    secrets=[
        "NEO4J_PASSWORD",
    ],
    with_files=[
        FileSpec(destination=f"/opt/scripts/{script_name}", content=script_content)
        for script_name, script_content in get_script_files().items()
    ],
)

# Register the tool (without priority parameter)
tool_registry.register("memory_management", list_memories_tool)

__all__ = ["list_memories_tool"] 