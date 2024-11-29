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

find_preference_tool = MemoryManagementTool(
    name="find_preference",
    description=(
        "🔍 Search for specific preferences or settings in your memory bank.\n\n"
        "This tool helps you find particular preferences by searching through both the content "
        "and tags of your stored memories. Perfect for checking if you've already set a "
        "preference for something specific.\n\n"
        "💡 To view all preferences, use the `load_memories` tool instead."
    ),
    content="""
set -e
python -m venv /opt/venv > /dev/null
. /opt/venv/bin/activate > /dev/null
pip install mem0ai langchain-community rank_bm25 2>&1 | grep -v '[notice]' > /dev/null

python /opt/scripts/find_preference_handler.py "{{ .search_query }}" || exit 1
""",
    args=[
        Arg(
            name="search_query",
            description=(
                "What preference are you looking for? Enter keywords or phrases to search for.\n"
                "**Examples**:\n"
                "- \"notification preferences\"\n"
                "- \"deployment settings\"\n"
                "- \"email alerts\""
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
        for script_name, script_content in get_script_files().items()
    ],
)

# Register the tool
tool_registry.register("memory_management", find_preference_tool) 