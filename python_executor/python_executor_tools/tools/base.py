"""Base tool for Python execution."""

from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.registry import tool_registry
import tempfile
import os
import subprocess
import shutil
import logging
from typing import Optional, List, Dict, Any

PYTHON_EXECUTOR_ICON = "https://img.icons8.com/color/512/python.png"
DOCKER_IMAGE = "python:3.12-slim-bookworm"  # Using slim-bookworm for better package management

logger = logging.getLogger(__name__)

class PythonExecutorTool(Tool):
    """Base class for Python execution tools."""
    
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        args: List[Arg],
        mermaid: str,
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

        # Add minimal setup script - only install essential packages
        setup_script = """
#!/bin/sh
set -e

# Function for logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Install only if command not available
if ! command -v jq >/dev/null 2>&1; then
    log "Installing jq..."
    apt-get update -qq >/dev/null 2>&1
    apt-get install -qq -y jq >/dev/null 2>&1
fi

# Install Python packages without cache
export PIP_NO_CACHE_DIR=1
"""
        
        full_content = setup_script + "\n" + content

        super().__init__(
            name=name,
            description=description,
            icon_url=PYTHON_EXECUTOR_ICON,
            type="docker",
            image=DOCKER_IMAGE,
            content=full_content,
            args=args,
            env=env,
            secrets=secrets,
            with_files=with_files,
            mermaid=mermaid
        )
        
        # Register the tool
        tool_registry.register(f"python_executor.{name}", self) 