from kubiya_sdk.tools import Tool, Arg, FileSpec
import os
from typing import List, Dict, Optional, Any, ClassVar
from pathlib import Path

DOCKER_ICON_URL = "https://www.docker.com/wp-content/uploads/2022/03/vertical-logo-monochromatic.png"

class DockerTool(Tool):
    """Base class for Docker tools with enhanced functionality and script management."""

    # Required environment variables for Kubernetes integration
    K8S_ENV: ClassVar[List[str]] = [
        "KUBERNETES_SERVICE_HOST",  # K8s API server host
        "KUBERNETES_SERVICE_PORT"   # K8s API server port
    ]

    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        args: List[Arg],
        env: Optional[List[str]] = None,
        secrets: Optional[List[str]] = None,
        with_files: Optional[List[FileSpec]] = None,
        mermaid: Optional[str] = None,
        long_running: bool = False,
    ):
        """Initialize a Docker tool with enhanced script management."""
        if env is None:
            env = []
        if secrets is None:
            secrets = []
        if with_files is None:
            with_files = []

        # Add Kubernetes environment variables if they exist
        env.extend([var for var in self.K8S_ENV if os.getenv(var)])

        # Add core utility scripts
        with_files.extend(self._get_core_scripts())

        # Wrap the main content with our script framework
        full_content = self._wrap_content(content)

        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="python:3.9-slim",
            content=full_content,
            args=args,
            env=env,
            secrets=secrets,
            with_files=with_files,
            icon_url=DOCKER_ICON_URL,
            mermaid=mermaid,
            long_running=long_running
        )

    def _get_core_scripts(self) -> List[FileSpec]:
        """Get the core utility scripts needed by all tools."""
        scripts_dir = Path(__file__).parent / "scripts"
        
        core_scripts = [
            ("utils.sh", "/tmp/scripts/utils.sh"),
            ("setup.sh", "/tmp/scripts/setup.sh"),
            ("git_utils.sh", "/tmp/scripts/git_utils.sh"),
            ("k8s_utils.sh", "/tmp/scripts/k8s_utils.sh"),
            ("dagger_setup.sh", "/tmp/scripts/dagger_setup.sh")
        ]
        
        file_specs = []
        
        # Add scripts
        for script_name, dest_path in core_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                with open(script_path, 'r') as f:
                    file_specs.append(
                        FileSpec(
                            destination=dest_path,
                            content=f.read()
                        )
                    )
            else:
                raise FileNotFoundError(f"Core script {script_name} not found at {script_path}")
        
        return file_specs

    def _wrap_content(self, content: str) -> str:
        """Wrap the tool's content with our script framework."""
        return f"""#!/bin/sh
set -e

# Source utility functions
. /tmp/scripts/utils.sh
. /tmp/scripts/git_utils.sh
. /tmp/scripts/k8s_utils.sh

# Function to cleanup on exit
cleanup() {{
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log "❌" "Script failed with exit code: $exit_code"
    fi
    exit $exit_code
}}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Install required packages
echo "🔧 Installing required packages..."
apt-get update -qq && apt-get install -y curl python3-pip jq netcat -qq > /dev/null 2>&1

# Setup kubectl and discover Dagger engine
. /tmp/scripts/dagger_setup.sh

# Install dagger SDK
echo "📦 Installing Dagger SDK..."
pip install dagger-io > /dev/null 2>&1

# Run setup script
. /tmp/scripts/setup.sh

# Main tool content
{content}
"""