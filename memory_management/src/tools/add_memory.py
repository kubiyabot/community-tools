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

add_memory_tool = MemoryManagementTool(
    name="add_memory",
    description=(
        "Add a new memory to the long-term memory store for the current user. "
        "This tool is useful for storing user preferences around resources and actions they like to consume. "
        "By adding these memories, you can personalize experiences based on user preferences in the future."
    ),
    content="""
set -e
python -m venv /opt/venv > /dev/null
. /opt/venv/bin/activate > /dev/null
pip install mem0ai 2>&1 | grep -v '[notice]' > /dev/null

# Run the add memory handler script
python /opt/scripts/add_memory_handler.py "{{ .memory_content }}" "{{ .tags }}"
""",
    args=[
        Arg(
            name="memory_content",
            description=(
                "The content of the memory to add. This should be a string representing the user's preference or behavior.\n"
                "**Example**: \"Prefers to receive notifications via email for deployment events\""
            ),
            required=True,
        ),
        Arg(
            name="tags",
            description=(
                "Optional tags to categorize the memory for better organization and retrieval. "
                "Provide the tags as a JSON array of strings.\n"
                "**Example**: '[\"notifications\", \"preferences\", \"email\"]'"
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
tool_registry.register("memory_management", add_memory_tool)

__all__ = ["add_memory_tool"] 