from kubiya_sdk.tools import Tool, FileSpec
import os
from pathlib import Path

ZOOM_ICON_URL = "https://seeklogo.com/images/Z/zoom-icon-logo-C552F99BAB-seeklogo.com.png"

class ZoomTool(Tool):
    def __init__(
        self,
        name,
        description,
        content,
        args=[],
        env=[],
        secrets=["ZOOM_API_KEY", "ZOOM_API_SECRET"],
        long_running=False,
        with_files=None,
        image="python:3.9-alpine",
        mermaid=None
    ):
        # Get the module directory path for helper scripts
        module_dir = Path(__file__).parent.parent
        
        # Basic environment setup script
        setup_script = """
        #!/bin/sh
        set -e

        echo "🔍 Preparing Zoom environment..."
        
        # Validate required secrets
        if [ -z "$ZOOM_API_KEY" ] || [ -z "$ZOOM_API_SECRET" ]; then
            echo "❌ Error: ZOOM_API_KEY and ZOOM_API_SECRET are required"
            echo "Please configure these in your Kubiya environment settings"
            exit 1
        fi
        
        # Create runtime directories
        mkdir -p /tmp/zoom_tools/handlers

        # Install system dependencies
        if ! apk add --no-cache curl jq python3-dev build-base > /dev/null 2>&1; then
            echo "❌ Failed to install system dependencies"
            exit 1
        fi

        # Install Python packages with better error handling
        echo "📦 Installing required Python packages..."
        if ! pip install --no-cache-dir 'zoomus>=1.1.5' requests python-dateutil pytz markdown tabulate > /dev/null 2>&1; then
            echo "❌ Failed to install Python dependencies"
            exit 1
        fi

        # Make handlers executable
        chmod +x /tmp/zoom_tools/handlers/*.py

        # Add zoom_tools to Python path
        export PYTHONPATH="/tmp:$PYTHONPATH"

        echo "✅ Environment ready"
        """
        
        # Combine setup script with main content
        full_content = setup_script + "\n" + content.replace('/usr/local/lib/zoom_tools', '/tmp/zoom_tools')

        # Add helper scripts as files
        helper_files = [
            FileSpec(
                destination="/tmp/zoom_tools/zoom_helpers.py",
                source=str(module_dir / "scripts" / "zoom_helpers.py")
            ),
            FileSpec(
                destination="/tmp/zoom_tools/zoom_formatters.py",
                source=str(module_dir / "scripts" / "zoom_formatters.py")
            ),
            FileSpec(
                destination="/tmp/zoom_tools/zoom_operations.py",
                source=str(module_dir / "scripts" / "zoom_operations.py")
            ),
            FileSpec(
                destination="/tmp/zoom_tools/handlers/meeting_handler.py",
                source=str(module_dir / "scripts" / "handlers" / "meeting_handler.py")
            ),
            FileSpec(
                destination="/tmp/zoom_tools/handlers/webinar_handler.py",
                source=str(module_dir / "scripts" / "handlers" / "webinar_handler.py")
            ),
            FileSpec(
                destination="/tmp/zoom_tools/handlers/user_handler.py",
                source=str(module_dir / "scripts" / "handlers" / "user_handler.py")
            ),
            FileSpec(
                destination="/tmp/zoom_tools/__init__.py",
                content="""
from .zoom_helpers import *
from .zoom_formatters import *
from .zoom_operations import *
"""
            )
        ]

        # Combine provided files with helper files
        if with_files:
            with_files.extend(helper_files)
        else:
            with_files = helper_files

        super().__init__(
            name=name,
            description=description,
            icon_url=ZOOM_ICON_URL,
            type="docker",
            image=image,
            content=full_content,
            args=args,
            env=env,
            secrets=secrets,
            long_running=long_running,
            with_files=with_files,
            mermaid=mermaid
        )