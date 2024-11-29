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

delete_memory_tool = MemoryManagementTool(
    name="delete_memory",
    description=(
        "Delete a stored user preference from the long-term memory store based on its ID. "
        "Use this tool when a user's preference has changed or is no longer valid."
    ),
    content="""
set -e
python -m venv /opt/venv > /dev/null
. /opt/venv/bin/activate > /dev/null
pip install mem0ai langchain-community 2>&1 | grep -v '[notice]' > /dev/null

# Run the delete memory handler script
python /opt/scripts/delete_memory_handler.py "{{ .memory_id }}"
""",
    args=[
        Arg(
            name="memory_id",
            description=(
                "The ID of the memory to delete. You can obtain the memory ID from the output of the `list_memories` tool.\n"
                "**Example**: \"bf4d4092-cf91-4181-bfeb-b6fa2ed3061b\""
            ),
            required=True,
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
tool_registry.register("memory_management", delete_memory_tool)

__all__ = ["delete_memory_tool"] 