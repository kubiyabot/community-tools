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

# Import all scripts from the scripts directory
scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
script_files = {}
for script_path in scripts_dir.glob("*.py"):
    with open(script_path, "r") as f:
        script_files[script_path.name] = f.read()

list_memories_tool = MemoryManagementTool(
    name="list_memories",
    description=(
        "List all stored user preferences for the current user. "
        "This tool helps in reviewing long-term memories about user preferences around resources and actions they like to consume. "
        "You can filter memories by tags to focus on specific categories."
    ),
    content="""
set -e
python -m venv /opt/venv > /dev/null
. /opt/venv/bin/activate > /dev/null
pip install mem0ai 2>&1 | grep -v '[notice]' > /dev/null

# Run the list memories handler script
python /opt/scripts/list_memories_handler.py "{{ .tags }}"
""",
    args=[
        Arg(
            name="tags",
            description=(
                "Optional tags to filter memories. Only preferences containing all the specified tags will be listed. "
                "Provide the tags as a JSON array of strings.\n"
                "**Example**: '[\"notifications\"]'"
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
        for script_name, script_content in script_files.items()
    ],
)

# Register the tool
tool_registry.register("memory_management", list_memories_tool)

__all__ = ["list_memories_tool"] 