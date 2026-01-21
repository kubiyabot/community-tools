from kubiya_workflow_sdk.tools import Tool, Arg
from typing import Dict, Any, List, Optional
from pydantic import root_validator
import logging
import json

logger = logging.getLogger(__name__)

class TerraformModuleTool(Tool):
    """Tool for managing Terraform modules."""

    def __init__(
        self,
        name: str,
        description: str,
        module_config: Dict[str, Any],
        action: str,
        with_pr: bool = False,
        mermaid: Optional[Dict[str, str]] = None
    ):
        """Initialize the tool with proper schema validation."""
        try:
            # Validate module config
            if not isinstance(module_config, dict):
                raise ValueError("module_config must be a dictionary")
            
            required_fields = ['name', 'description', 'source']
            for field in required_fields:
                if field not in module_config:
                    raise ValueError(f"module_config missing required field: {field}")
                
            if not isinstance(module_config['source'], dict):
                raise ValueError("module_config['source'] must be a dictionary")
                
            if 'location' not in module_config['source']:
                raise ValueError("module_config['source'] missing required field: location")

            # Create base args
            args = [
                Arg(
                    name="variables",
                    description="Variables for the Terraform module",
                    type="dict",
                    required=False,
                    default="{}"
                )
            ]

            # Create mermaid diagram if not provided
            if not mermaid:
                mermaid = {
                    'graph': f"""
                        graph TD
                            A[Start] --> B[Load {action.title()} Configuration]
                            B --> C[Validate Variables]
                            C --> D[Execute {action.title()}]
                            D --> E[Process Results]
                            E --> F[End]
                    """
                }

            # Create action description
            action_desc = {
                'plan': 'Plan infrastructure changes for',
                'apply': 'Apply infrastructure changes to',
                'plan_pr': 'Plan infrastructure changes and create PR for'
            }
            
            current_action = 'plan_pr' if action == 'plan' and with_pr else action
            
            tool_description = (
                f"{action_desc[current_action]} {module_config['description']} "
                f"(source: {module_config['source']['location']}) - "
                f"version: {module_config['source'].get('version', 'latest')}"
            )

            # Initialize base tool
            super().__init__(
                name=name,
                description=tool_description,
                args=args,
                env=[
                    "SLACK_CHANNEL_ID",
                    "SLACK_THREAD_TS",
                    "KUBIYA_USER_EMAIL"
                ],
                secrets=[
                    "SLACK_API_TOKEN",
                    "GH_TOKEN"
                ],
                type="docker",
                image="hashicorp/terraform:latest",
                handler=self.handle_terraform_module,
                mermaid=mermaid
            )

            # Store module-specific configurations
            self.module_config = module_config
            self.action = action
            self.with_pr = with_pr

        except Exception as e:
            logger.error(f"Failed to initialize TerraformModuleTool: {str(e)}")
            raise ValueError(f"Tool initialization failed: {str(e)}")

    async def handle_terraform_module(self, **kwargs) -> Dict[str, Any]:
        """Handle Terraform module operations."""
        try:
            # Basic validation
            if not self.module_config:
                raise ValueError("No module configuration available")

            # Process variables
            variables = kwargs.get('variables', {})
            if isinstance(variables, str):
                try:
                    variables = json.loads(variables)
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON in variables parameter")

            # Return basic success response for now
            return {
                'success': True,
                'action': self.action,
                'module': self.module_config['name'],
                'variables': variables
            }

        except Exception as e:
            logger.error(f"Failed to handle terraform module: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    class Config:
        arbitrary_types_allowed = True
