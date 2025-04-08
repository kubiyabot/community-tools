from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg

class MonitoringTool(Tool):
    """Base class for all monitoring tools."""
    
    def __init__(self, name: str, description: str, content: str, args: List[Arg] = None, 
                 image: str = "alpine:latest", icon_url: str = None, secrets: List[str] = [], env: List[str] = [],
                 long_running: bool = False, mermaid_diagram: str = None):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args or [],
            image=image,
            icon_url=icon_url,
            type="docker",
            secrets=secrets,
            env=env,
            long_running=long_running,
            mermaid_diagram=mermaid_diagram
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
    """Base class for Grafana tools using Bash."""
    
    def __init__(self, name: str, description: str, content: str, args: List[Arg] = None):
        # No need for install_packages since we'll install jq directly in the tools
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            image="curlimages/curl:latest",
            secrets=["GRAFANA_API_TOKEN"],
            env=["GRAFANA_HOST"]
        )

class AwsBaseTool(MonitoringTool):
    """Base class for AWS tools using the AWS CLI."""
    
    def __init__(self, name: str, description: str, content: str, args: List[Arg] = None, 
                 long_running: bool = False, mermaid_diagram: str = None):
        # Add common AWS icon URL
        aws_icon = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Amazon_Web_Services_Logo.svg/2560px-Amazon_Web_Services_Logo.svg.png"
        
        # Add LocalStack endpoint configuration if needed
        localstack_content = """
        # Configure AWS CLI endpoint if AWS_ENDPOINT_URL is set
        if [ ! -z "$AWS_ENDPOINT_URL" ]; then
            ENDPOINT_ARGS="--endpoint-url $AWS_ENDPOINT_URL"
        else
            ENDPOINT_ARGS=""
        fi
        
        # Replace aws commands with endpoint configuration
        """ + content.replace("aws ", "aws $ENDPOINT_ARGS ")
        
        super().__init__(
            name=name,
            description=description,
            content=localstack_content,
            args=args or [],
            image="amazon/aws-cli:latest",
            icon_url=aws_icon,
            env=["AWS_DEFAULT_REGION", "AWS_ENDPOINT_URL", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
            long_running=long_running,
            mermaid_diagram=mermaid_diagram
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