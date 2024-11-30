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

delete_memory_tool = MemoryManagementTool(
    name="delete_memory",
    description=(
        "Delete a stored user preference from memory based on its ID. "
        "Use this tool when a user's preference has changed or is no longer valid."
    ),
    content="""
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
    ],
    secrets=[
        "MEM0_API_KEY",
    ],
    with_files=[
        FileSpec(destination=f"/opt/scripts/{script_name}", content=script_content)
        for script_name, script_content in get_script_files().items()
    ],
)

# Register the tool
tool_registry.register("memory_management", delete_memory_tool)

__all__ = ["delete_memory_tool"] 