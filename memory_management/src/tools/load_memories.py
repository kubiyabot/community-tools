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
from ..utils import get_script_files

load_memories_tool = MemoryManagementTool(
    name="load_memories",
    description=(
        "🎯 [Recommended First Step] Load all your stored preferences and settings!\n\n"
        "This tool helps me understand your previous choices by loading all your stored preferences. "
        "Running this at the start of our conversation ensures I can provide personalized assistance "
        "based on your past preferences.\n\n"
        "💡 For searching specific preferences, use the `find_preference` tool instead."
    ),
    content="""
set -e
python -m venv /opt/venv > /dev/null
. /opt/venv/bin/activate > /dev/null
pip install mem0ai==1.1.0 2>&1 | grep -v '[notice]' > /dev/null

python /opt/scripts/load_memories_handler.py || exit 1
""",
    args=[],  # No arguments needed - just loads everything
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
tool_registry.register("memory_management", load_memories_tool) 