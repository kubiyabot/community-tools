"""Jupyter notebook execution tool."""

from kubiya_workflow_sdk.tools import Arg
from .base import PythonExecutorTool

class JupyterExecutor(PythonExecutorTool):
    """Jupyter notebook execution tool."""
    
    def __init__(self):
        super().__init__(
            name="jupyter",
            description="""Execute Jupyter notebooks with optional dependencies.
        
Notebook Format (JSON):
{
    "cells": [
        {
            "cell_type": "code",
            "source": "print('Hello World')",
            "metadata": {}
        }
    ],
    "metadata": {
        "kernelspec": {
            "name": "python3"
        }
    }
}""",
            content="""
#!/bin/sh
set -e  # Exit on any error

# Enable error handling
error_handler() {
    echo "Error occurred in script at line: ${1}" >&2
    exit 1
}
trap 'error_handler ${LINENO}' ERR

# Function for logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Validate input
if [ -z "$NOTEBOOK" ]; then
    log "ERROR: No notebook content provided"
    exit 1
fi

# Create temporary directory with error handling
TEMP_DIR=$(mktemp -d) || { log "ERROR: Failed to create temporary directory"; exit 1; }
log "Created temporary directory: $TEMP_DIR"
cd "$TEMP_DIR" || { log "ERROR: Failed to change to temporary directory"; exit 1; }

# Install Jupyter and dependencies
log "Installing Jupyter dependencies..."
pip install nbformat nbconvert jupyter_client ipykernel 2>&1 || { 
    log "ERROR: Failed to install Jupyter dependencies"
    exit 1
}
log "Successfully installed Jupyter dependencies"

# Install additional requirements if provided
if [ ! -z "$REQUIREMENTS" ]; then
    log "Installing additional requirements..."
    pip install $REQUIREMENTS 2>&1 || { 
        log "ERROR: Failed to install additional requirements"
        exit 1
    }
    log "Successfully installed additional requirements"
fi

# Create notebook file
log "Creating notebook file..."
echo "$NOTEBOOK" > notebook.ipynb || { log "ERROR: Failed to create notebook file"; exit 1; }

# Set up kernel
KERNEL_NAME=${KERNEL_NAME:-python3}
log "Setting up Jupyter kernel: $KERNEL_NAME"
python -m ipykernel install --user --name "$KERNEL_NAME" 2>&1 || {
    log "ERROR: Failed to install Jupyter kernel"
    exit 1
}
log "Successfully installed Jupyter kernel"

# Execute notebook
log "Executing notebook..."
jupyter nbconvert --to notebook --execute \
    --ExecutePreprocessor.kernel_name="$KERNEL_NAME" \
    --ExecutePreprocessor.timeout=600 \
    --stdout notebook.ipynb 2>&1 || {
    log "ERROR: Failed to execute notebook"
    exit 1
}
log "Notebook execution completed successfully"

# Cleanup
log "Cleaning up..."
cd / || { log "ERROR: Failed to leave temporary directory"; exit 1; }
rm -rf "$TEMP_DIR" || { log "WARNING: Failed to clean up temporary directory: $TEMP_DIR"; }
log "Cleanup completed"
""",
            args=[
                Arg(
                    name="notebook",
                    type="str",
                    description="The Jupyter notebook content in JSON format",
                    required=True
                ),
                Arg(
                    name="requirements",
                    type="str",
                    description="Space-separated list of pip requirements to install",
                    required=False
                ),
                Arg(
                    name="kernel_name",
                    type="str",
                    description="The name of the Jupyter kernel to use (default: python3)",
                    required=False
                )
            ]
        )

# Create singleton instance
jupyter_executor = JupyterExecutor()