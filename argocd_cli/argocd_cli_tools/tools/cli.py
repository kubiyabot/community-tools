from typing import List
import sys
from .base import ArgoCDCLITool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CLITools:
    """ArgoCD CLI wrapper tools."""

    def __init__(self):
        """Initialize and register all ArgoCD CLI tools."""
        try:
            tools = [
                self.run_cli_command()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("argocd_cli", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register ArgoCD CLI tools: {str(e)}", file=sys.stderr)
            raise

    def run_cli_command(self) -> ArgoCDCLITool:
        """Execute an ArgoCD CLI command."""
        return ArgoCDCLITool(
            name="argocd_cli_command",
            description="Execute any ArgoCD CLI command",
            content="""
            # Validate required parameters
            if [ -z "$command" ]; then
                echo "Error: Command is required"
                exit 1
            fi
            
            echo "=== Executing ArgoCD CLI Command ==="
            echo "Command: argocd $command"
            echo ""
            
            # Execute the command
            argocd $command
            """,
            args=[
                Arg(name="command", description="The command to pass to the ArgoCD CLI (e.g., 'app list', 'project create my-project')", required=True)
            ],
            image="argoproj/argocd:latest"
        ) 