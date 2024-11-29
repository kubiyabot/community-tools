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

search_memories_tool = MemoryManagementTool(
    name="search_memories",
    description=(
        "Search stored user preferences based on a query string. "
        "This tool is helpful when you want to retrieve specific preferences or behaviors the user has expressed, enabling personalized interactions."
    ),
    content="""
set -e
python -m venv /opt/venv > /dev/null
. /opt/venv/bin/activate > /dev/null
pip install mem0ai langchain-community rank_bm25 neo4j 2>&1 | grep -v '[notice]' > /dev/null

# Run the search memories handler script
python /opt/scripts/search_memories_handler.py "{{ .query }}"
""",
    args=[
        Arg(
            name="query",
            description=(
                "The search query to find related user preferences. Provide a string representing your search terms.\n"
                "**Example**: \"Preferences for receiving notifications\""
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
tool_registry.register("memory_management", search_memories_tool)

__all__ = ["search_memories_tool"] 