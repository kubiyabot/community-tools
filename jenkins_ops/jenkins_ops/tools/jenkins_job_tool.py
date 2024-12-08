import logging
import time
from typing import Dict, Any, Optional
from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.models import FileSpec
from pydantic import Field
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class JenkinsJobTool(Tool):
    """Tool for executing and monitoring Jenkins jobs."""
    
    job_config: Dict[str, Any]
    long_running: bool = False
    poll_interval: int = Field(default=30, description="Interval in seconds to poll job status")
    stream_logs: bool = Field(default=True, description="Stream job logs while running")
    
    def __init__(self, **data):
        """Initialize the Jenkins job tool with configuration."""
        super().__init__(**data)
        
        # Add standard environment variables and secrets
        self.env = (self.env or []) + ["JENKINS_URL"]
        self.secrets = (self.secrets or []) + ["JENKINS_API_TOKEN"]
        
        # Set default icon
        if not self.icon_url:
            self.icon_url = "https://e7.pngegg.com/pngimages/285/944/png-clipart-jenkins-software-build-continuous-integration-plug-in-software-testing-github-child-face-thumbnail.png"
            
        # Generate mermaid diagram for job flow
        self.mermaid = self._generate_mermaid_diagram()

    def _generate_mermaid_diagram(self) -> str:
        """Generate a mermaid diagram showing the job execution flow."""
        return """
        sequenceDiagram
            participant U as User
            participant K as Kubiya
            participant J as Jenkins
            
            U->>K: Request job execution
            K->>J: Trigger build
            
            alt Long Running Job
                loop Job Status
                    K->>J: Poll status
                    J-->>K: Current status
                end
            else Regular Job
                J-->>K: Build result
            end
            
            K-->>U: Final status
        """

    def _generate_script_content(self) -> str:
        """Generate the script content for job execution."""
        return """#!/bin/sh
set -e

# Validate environment
if [ -z "$JENKINS_URL" ]; then
    echo "❌ JENKINS_URL environment variable is required"
    exit 1
fi

if [ -z "$JENKINS_API_TOKEN" ]; then
    echo "❌ JENKINS_API_TOKEN environment variable is required"
    exit 1
fi

# Install dependencies
pip install -q python-jenkins requests

# Run job
python3 /opt/scripts/jenkins_job_runner.py
"""

    def prepare(self) -> None:
        """Prepare the tool for execution."""
        try:
            # Convert job parameters to Kubiya args
            self.args = []
            
            # Get parameters from job config
            for param_name, param_config in self.job_config.get('parameters', {}).items():
                if not param_name:  # Skip parameters without names
                    continue
                    
                # Create argument
                arg = Arg(
                    name=param_name,
                    type=param_config.get('type', 'str'),
                    description=param_config.get('description', ''),
                    required=param_config.get('required', True)
                )
                
                # Handle default values
                if 'default' in param_config:
                    default_value = param_config['default']
                    if param_config.get('type') == 'bool':
                        arg.default = str(default_value).lower()
                    elif isinstance(default_value, (dict, list)):
                        arg.default = json.dumps(default_value)
                    else:
                        arg.default = str(default_value)
                
                self.args.append(arg)

            # Set up script content
            self.content = self._generate_script_content()
            
            # Add required files
            self.with_files = [
                FileSpec(
                    destination="/opt/scripts/jenkins_job_runner.py",
                    source=str(Path(__file__).parent.parent / 'scripts' / 'jenkins_job_runner.py')
                ),
                FileSpec(
                    destination="/tmp/jenkins_config.json",
                    content=json.dumps({
                        'username': self.job_config['auth']['username'],
                        'job_name': self.job_config['name'],
                        'stream_logs': self.stream_logs,
                        'poll_interval': self.poll_interval,
                        'parameters': {
                            name: {
                                'type': self.job_config['parameters'][name].get('type', 'str'),
                                'name': name
                            }
                            for name in self.job_config['parameters']
                        }
                    })
                )
            ]
        except Exception as e:
            logger.error(f"Failed to prepare tool: {str(e)}")
            raise
        