import inspect
import sys
import os
from pathlib import Path
import json

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
        "Add a new memory to the graph memory store for the current user. "
        "This tool stores user preferences and can extract entities using optional custom prompts. "
        "The stored memories can be used to personalize future interactions."
    ),
    content="""
set -e
python -m venv /opt/venv > /dev/null
. /opt/venv/bin/activate > /dev/null
pip install mem0ai 2>&1 | grep -v '[notice]' > /dev/null

# Run the add memory handler script with error handling
python /opt/scripts/add_memory_handler.py \
    "{{ .memory_content }}" \
    {{ if .tags }}"{{ .tags }}"{{ else }}""{{ end }} \
    {{ if .custom_prompt }}"{{ .custom_prompt }}"{{ end }} || exit 1
""",
    args=[
        Arg(
            name="memory_content",
            description=(
                "The content of the memory to add. This should be a string representing the user's preference or behavior.\n"
                "**Example**: \"Prefers to receive notifications via email for deployment events\""
            ),
            required=True,
            validate=lambda x: bool(x.strip()),
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
            validate=lambda x: x is None or (
                isinstance(x, str) and 
                all(isinstance(tag, str) for tag in json.loads(x))
            ),
        ),
        Arg(
            name="custom_prompt",
            description=(
                "Optional custom prompt for entity extraction. Use this to guide the extraction of specific types of entities.\n"
                "**Example**: \"Please only extract entities containing deployment-related relationships.\""
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