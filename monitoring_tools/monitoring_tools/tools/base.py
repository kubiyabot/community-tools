from typing import List, Optional, Dict, Any, Set
from kubiya_sdk.tools import Tool, Arg, FileSpec
from abc import ABC, abstractmethod

class MonitoringTool(Tool):
    """Base class for all monitoring tools."""
    
    def __init__(self, name: str, description: str, content: str, args: List[Arg] = None, 
                 image: str = "alpine:latest", icon_url: str = None, secrets: List[str] = [], env: List[str] = []):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args or [],
            image=image,
            icon_url=icon_url,
            type="docker",
            secrets=secrets,
            env=env
        )

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """Validate the provided arguments."""
        required_args = [arg.name for arg in self.args if arg.required]
        return all(arg in args and args[arg] for arg in required_args)

    def get_error_message(self, args: Dict[str, Any]) -> Optional[str]:
        """Return error message if arguments are invalid."""
        missing_args = []
        for arg in self.args:
            if arg.required and (arg.name not in args or not args[arg.name]):
                missing_args.append(arg.name)
        
        if missing_args:
            return f"Missing required arguments: {', '.join(missing_args)}"
        return None

class SlackBaseTool(MonitoringTool):
    """Base class for Slack tools using the Python SDK."""
    
    def __init__(self, name: str, description: str, content: str, args: List[Arg] = None):
        install_packages = """
        # Install Slack SDK
        pip install --no-cache-dir slack-sdk
        """
        content = install_packages + "\n" + content
        
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            image="python:3.9-slim",
            secrets=["SLACK_API_TOKEN"]
        )

class GrafanaBaseTool(MonitoringTool):
    """Base class for Grafana tools using the Python API."""
    
    def __init__(self, name: str, description: str, content: str, args: List[Arg] = None):
        install_packages = """
        # Install Grafana API client
        pip install --no-cache-dir grafana-api python-dateutil
        """
        content = install_packages + "\n" + content
        
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            image="python:3.9-slim",
            secrets=["GRAFANA_API_TOKEN"],
            env=["GRAFANA_HOST"]
        )

class AwsBaseTool(MonitoringTool):
    """Base class for AWS tools using the AWS CLI."""
    
    def __init__(self, name: str, description: str, content: str, args: List[Arg] = None):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            image="amazon/aws-cli:latest",
            secrets=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
            env=["AWS_REGION"]
        )

class GitHubBaseTool(MonitoringTool):
    """Base class for GitHub tools using the GitHub CLI."""
    
    def __init__(self, name: str, description: str, content: str, args: List[Arg] = None):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            image="ghcr.io/cli/cli:latest",
            secrets=["GITHUB_TOKEN"]
        )

# Common argument mixins
class LoggingArgsMixin:
    """Mixin to add common logging arguments."""
    
    def add_common_log_args(self):
        common_args = [
            Arg(name="start_time", description="Start time for log search", required=False),
            Arg(name="end_time", description="End time for log search", required=False),
            Arg(name="limit", description="Maximum number of logs to return", required=False)
        ]
        self.args.extend(common_args)

class MetricsArgsMixin:
    """Mixin to add common metrics arguments."""
    
    def add_common_metric_args(self):
        common_args = [
            Arg(name="metric_name", description="Name of the metric to query", required=True),
            Arg(name="period", description="Time period for metrics", required=False),
            Arg(name="statistics", description="Statistical functions to apply", required=False)
        ]
        self.args.extend(common_args) 