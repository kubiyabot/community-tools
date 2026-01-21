"""Base tool for Python execution."""

from kubiya_workflow_sdk.tools import Tool, Arg
from kubiya_workflow_sdk.tools.registry import tool_registry
import tempfile
import os
import subprocess
import shutil
import logging
from typing import Optional, List, Dict, Any

PYTHON_EXECUTOR_ICON = "https://img.icons8.com/color/512/python.png"

logger = logging.getLogger(__name__)

class PythonExecutorTool(Tool):
    """Base class for Python execution tools."""
    
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        args: List[Arg],
        env: Optional[List[str]] = None,
        secrets: Optional[List[str]] = None,
        with_files: Optional[List[str]] = None,
    ):
        if env is None:
            env = []
        if secrets is None:
            secrets = []
        if with_files is None:
            with_files = []

        # Add setup script to install virtualenv
        setup_script = """
        #!/bin/sh
        set -e
        pip install virtualenv > /dev/null
        """
        
        full_content = setup_script + "\n" + content

        super().__init__(
            name=name,
            description=description,
            icon_url=PYTHON_EXECUTOR_ICON,
            type="docker",
            image="python:3.12-slim",
            content=full_content,
            args=args,
            env=env,
            secrets=secrets,
            with_files=with_files
        )
        
        # Register the tool
        tool_registry.register(f"python_executor.{name}", self) 